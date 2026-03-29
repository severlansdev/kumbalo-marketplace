"""
Router de Trámites - Gestión de procesos legales y burocráticos de Kumbalo.
Incluye el flujo de Traspaso Express con integración de pasarela de pago.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
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
