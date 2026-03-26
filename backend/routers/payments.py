from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])

# Precios estáticos (Mock)
PRECIOS = {
    "pro_subscription": 150000,
    "turbo_sell": 50000,
    "weekly_bump": 20000
}

@router.post("/checkout/pro")
def simulate_pro_checkout(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Simula una compra de la suscripción PRO (Concesionario Avanzado)"""
    if current_user.is_pro:
        raise HTTPException(status_code=400, detail="El usuario ya tiene una suscripción PRO activa")

    # En la vida real, aquí se crearía un intento de pago con Stripe/Paypal y se devolvería el client_secret
    # Simularemos la confirmación directa del pago
    
    current_user.is_pro = True
    db.commit()

    return {
        "status": "success",
        "message": "Pago exitoso. Ahora eres un usuario PRO.",
        "amount_charged": PRECIOS["pro_subscription"],
        "currency": "COP"
    }

@router.post("/checkout/boost/{moto_id}")
def simulate_boost_checkout(moto_id: int, package: str = "turbo_sell", db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Simula comprar visibilidad adicional para una moto específica"""
    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
    
    if not moto:
        raise HTTPException(status_code=404, detail="La motocicleta no existe")
    
    if moto.propietario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No tienes permiso para destacar esta moto")

    if package not in PRECIOS:
        raise HTTPException(status_code=400, detail="Paquete de boosting inválido")
    
    if moto.is_hot and package == "turbo_sell":
        raise HTTPException(status_code=400, detail="Esta moto ya posee un Turbo Sell activo")

    # Modificamos la propiedad y guardamos
    moto.is_hot = True
    db.commit()

    return {
        "status": "success",
        "message": f"Pago exitoso para el paquete {package}. Tu moto es ahora destacada.",
        "amount_charged": PRECIOS[package],
        "currency": "COP"
    }
