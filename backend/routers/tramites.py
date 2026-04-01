"""
Router de Trámites - Gestión de procesos legales y burocráticos de Kumbalo.
Incluye el flujo de Traspaso Express con integración de pasarela de pago.
"""
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List
import json
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..aws_s3 import upload_image_to_s3
from ..utils.contract_generator import generate_purchase_contract
import mercadopago
import os

router = APIRouter(prefix="/tramites", tags=["trámites"])

# Inicialización de MercadoPago SDK
# Se utiliza para generar links de pago dinámicos para el servicio de traspaso.
sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN", "APP_USR-6317427424180639-030916-7c0d6b5836c0f0d23f381c0e12dcf6e6-173616652"))

@router.post("/solicitar", response_model=schemas.TramiteResponse)
async def solicitar_tramite(
    request: schemas.TramiteCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
) -> models.Tramite:
    """
    Inicia el flujo de Traspaso Express Kumbalo ($440.000 COP).
    
    Este endpoint valida que la motocicleta exista, pertenezca a una zona con cobertura 
    (Bogotá/Medellín) y genera una preferencia de pago en MercadoPago.
    
    Args:
        request: Datos del trámite (moto_id, tipo).
        db: Sesión de base de datos.
        current_user: Usuario autenticado (será el comprador).
        
    Returns:
        models.Tramite: Objeto del trámite creado con la URL de pago inyectada.
    """
    moto = db.query(models.Moto).filter(models.Moto.id == request.moto_id).first()
    
    if not moto:
        raise HTTPException(status_code=404, detail="Motocicleta no encontrada")

    # Validación de Alcance Regional (Solo Bogotá y Medellín por ahora)
    ciudades_soportadas = ["bogota", "bogotá", "medellin", "medellín"]
    ciudad_moto = (moto.ciudad or "").lower().strip()
    
    if ciudad_moto not in ciudades_soportadas:
        raise HTTPException(
            status_code=400, 
            detail=f"El servicio de Traspaso Express aún no está disponible en {moto.ciudad}. Por ahora operamos exclusivamente en Bogotá y Medellín."
        )
        
    # Verificar trámites activos
    tramite_previo = db.query(models.Tramite).filter(models.Tramite.moto_id == request.moto_id).first()
    if tramite_previo and tramite_previo.estado != "finalizado":
        return tramite_previo # Retornar el existente si no ha terminado

    # 1. Crear el objeto Trámite en estado inicial
    nuevo_tramite = models.Tramite(
        moto_id=moto.id,
        vendedor_id=moto.propietario_id,
        comprador_id=current_user.id,
        tipo=request.tipo,
        estado="pago_pendiente",
        costo_total=440000.0
    )
    
    db.add(nuevo_tramite)
    db.commit()
    db.refresh(nuevo_tramite)

    # 2. Generar Preferencia de Pago
    preference_data = {
        "items": [
            {
                "title": f"Traspaso Express Kumbalo: {moto.marca} {moto.modelo}",
                "quantity": 1,
                "unit_price": 440000.0,
                "currency_id": "COP"
            }
        ],
        "payer": {
            "email": current_user.email,
            "name": current_user.nombre
        },
        "back_urls": {
            "success": f"{os.getenv('FRONTEND_URL', 'https://kumbalo-marketplace.vercel.app')}/dashboard.html?tramite=pago_exitoso",
            "failure": f"{os.getenv('FRONTEND_URL', 'https://kumbalo-marketplace.vercel.app')}/dashboard.html?tramite=error"
        },
        "auto_return": "approved",
        "external_reference": f"tramite_{nuevo_tramite.id}_{current_user.id}"
    }

    try:
        preference_response = sdk.preference().create(preference_data)
        
        # Validar respuesta exitosa (200 o 201)
        if preference_response["status"] not in [200, 201]:
            error_status = preference_response["status"]
            error_resp = preference_response.get("response", {})
            error_msg = error_resp.get("message", "Error desconocido")
            
            # Feedback específico para errores de autenticación
            if error_status == 401:
                detail = "Error de Configuración Fintech: El Access Token de MercadoPago es inválido o ha expirado. Por favor contacta al administrador."
            else:
                detail = f"MercadoPago Error ({error_status}): {error_msg}"
                
            raise HTTPException(status_code=400, detail=detail)
            
        preference = preference_response["response"]
        
        # Guardar el ID de preferencia como pago_id temporal
        nuevo_tramite.pago_id = preference["id"]
        db.commit()
        
        # Inyectar el init_point para el frontend (Pydantic lo mapeará a pago_url)
        setattr(nuevo_tramite, 'pago_url', preference["init_point"])
        
        # 3. GENERACIÓN AUTOMÁTICA DE CONTRATO (Borrador inicial)
        try:
            await _generar_y_subir_contrato(nuevo_tramite, db)
        except Exception as e:
            print(f"Error generando contrato inicial: {e}")
            
        return nuevo_tramite
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado al generar link de pago: {str(e)}")

@router.get("/mis-tramites")
async def get_mis_tramites(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtiene la lista de trámites donde el usuario es comprador o vendedor"""
    return db.query(models.Tramite).filter(
        (models.Tramite.comprador_id == current_user.id) | 
        (models.Tramite.vendedor_id == current_user.id)
    ).all()

@router.get("/{tramite_id}", response_model=schemas.TramiteResponse)
async def get_tramite_detalle(
    tramite_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Ver el estatus detallado de un proceso de traspaso"""
    tramite = db.query(models.Tramite).filter(models.Tramite.id == tramite_id).first()
    if not tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    
    if current_user.id not in [tramite.comprador_id, tramite.vendedor_id] and current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes acceso a este trámite")
    
    return tramite


@router.post("/{tramite_id}/subir-documento", response_model=schemas.TramiteResponse)
async def subir_documento_tramite(
    tramite_id: int,
    tipo: str = Form(...), # contrato, poder, fun, cedula_comprador, cedula_vendedor
    archivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Sube un documento legal para el trámite a AWS S3.
    Actualiza el campo `documentos_json` del trámite.
    """
    from datetime import datetime
    
    tramite = db.query(models.Tramite).filter(models.Tramite.id == tramite_id).first()
    if not tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    
    # Validar que el usuario sea parte del trámite (comprador o vendedor)
    if current_user.id not in [tramite.comprador_id, tramite.vendedor_id] and current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para subir documentos a este trámite")

    # Subir a S3 usando la utilidad centralizada
    try:
        content_type = archivo.content_type or "application/octet-stream"
        url_s3 = upload_image_to_s3(archivo.file, archivo.filename, content_type)
        
        # Actualizar JSON de documentos
        docs_dict = {}
        if tramite.documentos_json:
            try:
                docs_dict = json.loads(tramite.documentos_json)
            except:
                docs_dict = {}
        
        docs_dict[tipo] = {
            "url": url_s3,
            "subido_por": current_user.nombre,
            "fecha": datetime.now().isoformat()
        }
        
        tramite.documentos_json = json.dumps(docs_dict)
        
        # Si ya se subieron los documentos clave, avanzar el estado
        claves = ["contrato", "poder", "fun", "cedula_comprador", "cedula_vendedor"]
        if all(k in docs_dict for k in claves) and tramite.estado == "documentos_pendientes":
            tramite.estado = "verificado_kumbalo"
            tramite.notas = f"Todos los documentos críticos han sido cargados. Pendiente verificación humana."

        db.commit()
        db.refresh(tramite)
        return tramite
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo el documento: {str(e)}")


@router.patch("/{tramite_id}/estado", response_model=schemas.TramiteResponse)
async def actualizar_estado_tramite(
    tramite_id: int,
    nuevo_estado: str = Form(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Permite a un administrador o gestor actualizar el estado del flujo.
    """
    if current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="Solo administradores pueden cambiar el estado manualmente")

    tramite = db.query(models.Tramite).filter(models.Tramite.id == tramite_id).first()
    if not tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")

    tramite.estado = nuevo_estado
    db.commit()
    db.refresh(tramite)
    return tramite


@router.post("/{tramite_id}/generar-contrato", response_model=schemas.TramiteResponse)
async def regenerar_contrato_tramite(
    tramite_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """
    Forzar la regeneración del contrato PDF con los datos actuales del perfil.
    Útil si el usuario actualizó su cédula o teléfono después de solicitar el trámite.
    """
    tramite = db.query(models.Tramite).filter(models.Tramite.id == tramite_id).first()
    if not tramite:
        raise HTTPException(status_code=404, detail="Trámite no encontrado")
    
    if current_user.id not in [tramite.comprador_id, tramite.vendedor_id] and current_user.rol != "admin":
        raise HTTPException(status_code=403, detail="No tienes acceso a este trámite")

    await _generar_y_subir_contrato(tramite, db)
    return tramite


async def _generar_y_subir_contrato(tramite: models.Tramite, db: Session):
    """Helper interno para generar PDF y subir a S3"""
    from datetime import datetime
    
    pdf_buffer = generate_purchase_contract(tramite)
    filename = f"contrato-compraventa-{tramite.id}.pdf"
    
    url_s3 = upload_image_to_s3(pdf_buffer, filename, "application/pdf")
    
    # Actualizar documentos_json
    docs_dict = {}
    if tramite.documentos_json:
        try:
            docs_dict = json.loads(tramite.documentos_json)
        except:
            docs_dict = {}
            
    docs_dict["contrato"] = {
        "url": url_s3,
        "subido_por": "SISTEMA_KUMBALO",
        "fecha": datetime.now().isoformat(),
        "es_borrador_auto": True
    }
    
    tramite.documentos_json = json.dumps(docs_dict)
    db.commit()
    db.refresh(tramite)
