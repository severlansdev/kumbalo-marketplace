import mercadopago
import os
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user
from ..utils import email_agent

router = APIRouter(prefix="/payments", tags=["payments"])

# Inicializar MercadoPago
sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN", "APP_USR-6317427424180639-030916-7c0d6b5836c0f0d23f381c0e12dcf6e6-173616652"))

@router.post("/create-preference/{moto_id}")
async def create_preference(
    moto_id: int, 
    db: Session = Depends(get_db), 
    current_user: models.Usuario = Depends(get_current_user)
):
    """Crea una preferencia de pago en MercadoPago para la comisión de una moto"""
    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
    
    if not moto:
        raise HTTPException(status_code=404, detail="Motocicleta no encontrada")
    
    if moto.propietario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para pagar la comisión de esta moto")

    # Determinar el monto de la comisión según la lógica de Kumbalo
    fee_amount = moto.commission_fee or 250000.0
    
    # Datos de la preferencia
    preference_data = {
        "items": [
            {
                "title": f"Comisión por venta: {moto.marca} {moto.modelo}",
                "quantity": 1,
                "unit_price": float(fee_amount),
                "currency_id": "COP"
            }
        ],
        "payer": {
            "email": current_user.email,
            "name": current_user.nombre
        },
        "back_urls": {
            "success": f"{os.getenv('FRONTEND_URL', 'https://kumbalo-marketplace.vercel.app')}/dashboard.html?payment=success",
            "failure": f"{os.getenv('FRONTEND_URL', 'https://kumbalo-marketplace.vercel.app')}/dashboard.html?payment=failure",
            "pending": f"{os.getenv('FRONTEND_URL', 'https://kumbalo-marketplace.vercel.app')}/dashboard.html?payment=pending"
        },
        "auto_return": "approved",
        "external_reference": f"moto_{moto.id}_{current_user.id}",
        "notification_url": f"{os.getenv('BACKEND_URL', 'https://kumbalo-api.vercel.app')}/api/payments/webhook"
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
                detail = "Error de Configuración Fintech: El Access Token de MercadoPago es inválido o ha expirado. Por favor contacta al administrador para actualizar las Secret Keys en Vercel."
            else:
                detail = f"MercadoPago Error ({error_status}): {error_msg}"
                
            raise HTTPException(status_code=400, detail=detail)
            
        preference = preference_response["response"]
        
        # Validar existencia de los campos necesarios
        if "id" not in preference or "init_point" not in preference:
            raise HTTPException(
                status_code=500, 
                detail="Respuesta incompleta de MercadoPago (falta ID o Punto de Inicio)"
            )
        
        # Registrar el intento de transacción como pendiente
        nueva_transaccion = models.Transaccion(
            vendedor_id=current_user.id,
            moto_id=moto.id,
            monto=fee_amount,
            tipo="comision_venta",
            estado="pendiente",
            referencia_pago=preference["id"],
            plataforma_pago="mercadopago"
        )
        db.add(nueva_transaccion)
        db.commit()

        return {
            "preference_id": preference["id"],
            "init_point": preference["init_point"]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error inesperado en Fintech: {str(e)}")

@router.post("/webhook")
async def mercadopago_webhook(request: Request, db: Session = Depends(get_db)):
    """Recibe notificaciones de MercadoPago (IPN/Webhooks) sobre el estado de los pagos"""
    data = await request.json()
    print(f"WEBHOOK RECIBIDO: {data}")
    
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        payment_info = sdk.payment().get(payment_id)
        payment_status = payment_info["response"].get("status")
        external_reference = payment_info["response"].get("external_reference")
        
        if payment_status == "approved" and external_reference:
            # Caso 1: Comisión de Venta (moto_ID_USERID)
            if external_reference.startswith("moto_"):
                parts = external_reference.split("_")
                if len(parts) >= 3:
                    moto_id = int(parts[1])
                    transaccion = db.query(models.Transaccion).filter(models.Transaccion.moto_id == moto_id).first()
                    if transaccion:
                        transaccion.estado = "completada"
                    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
                    if moto:
                        moto.commission_paid = True
                        moto.estado = "activa"
                    db.commit()
            
            # Caso 2: Traspaso Express (tramite_ID_USERID)
            elif external_reference.startswith("tramite_"):
                parts = external_reference.split("_")
                if len(parts) >= 3:
                    tramite_id = int(parts[1])
                    tramite = db.query(models.Tramite).filter(models.Tramite.id == tramite_id).first()
                    if tramite:
                        tramite.estado = "documentos_pendientes"
                        tramite.notas = f"Pago aprobado vía MercadoPago (Ref: {payment_id})"
                        db.commit()
                        
                        # Crear notificación para el usuario
                        nueva_notif = models.Notificacion(
                            usuario_id=tramite.comprador_id,
                            tipo="sistema",
                            titulo="Pago de Trámite Recibido",
                            contenido=f"Tu pago para el traspaso de la moto ha sido confirmado. Por favor carga los documentos necesarios.",
                            url=f"/dashboard.html?tramite_id={tramite.id}"
                        )
                        db.add(nueva_notif)
                        db.commit()
                        
                        # Disparar alerta transaccional por Email
                        email_agent.notify_traspaso_pagado(
                            comprador_email=tramite.comprador.email,
                            tramite_id=tramite.id
                        )
                
    return {"status": "ok"}
