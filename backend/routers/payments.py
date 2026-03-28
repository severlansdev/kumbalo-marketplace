import mercadopago
import os
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

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
        preference = preference_response["response"]
        
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
            "init_point": preference["init_point"] # El link de pago real
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creando preferencia de pago: {str(e)}")

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
            # Formato: moto_ID_USERID
            parts = external_reference.split("_")
            if len(parts) >= 3:
                moto_id = int(parts[1])
                
                # Actualizar transacción
                transaccion = db.query(models.Transaccion).filter(models.Transaccion.moto_id == moto_id).first()
                if transaccion:
                    transaccion.estado = "completada"
                
                # Activar el flag de pago en la moto
                moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
                if moto:
                    moto.commission_paid = True
                    moto.estado = "activa" # Aseguramos que esté visible
                
                db.commit()
                
    return {"status": "ok"}
