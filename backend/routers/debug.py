from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from ..database import get_db

router = APIRouter(prefix="/debug", tags=["debug"])

@router.get("/db-check")
def db_check(db: Session = Depends(get_db)):
    try:
        # Check tables
        tables = db.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public'")).fetchall()
        
        # Check columns of 'motos'
        motos_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='motos'")).fetchall()
        
        # Check columns of 'tramites'
        tramites_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='tramites'")).fetchall()
        
        # Check columns of 'usuarios'
        usuarios_cols = db.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='usuarios'")).fetchall()
        
        return {
            "status": "connected",
            "tables": [t[0] for t in tables],
            "motos_columns": [c[0] for c in motos_cols],
            "tramites_columns": [c[0] for c in tramites_cols],
            "usuarios_columns": [c[0] for c in usuarios_cols]
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@router.get("/seed")
def seed_db(db: Session = Depends(get_db)):
    try:
        from .. import models
        from ..utils.fees import calculate_kumbalo_fee
        
        # 1. Buscar o crear el Auditor
        auditor = db.query(models.Usuario).filter(models.Usuario.email == "auditor_qa@kumbalo.com").first()
        if not auditor:
            return {"status": "error", "message": "Debes registrar el usuario auditor_qa@kumbalo.com primero."}
        
        # 2. Crear la Yamaha MT-09
        moto = models.Moto(
            marca="Yamaha",
            modelo="MT-09 SP 2024",
            año=2024,
            precio=54900000.0,
            kilometraje=1200,
            cilindraje=890,
            color="Icon Performance",
            transmision="manual",
            combustible="gasolina",
            ciudad="Bogotá",
            descripcion="Auditoría QA - Moto de pruebas para Traspaso Express.",
            propietario_id=auditor.id,
            commission_fee=calculate_kumbalo_fee(54900000.0),
            commission_type="fixed",
            commission_paid=True, # Habilitar Traspaso de inmediato
            estado="activa"
        )
        db.add(moto)
        db.commit()
        db.refresh(moto)
        
        return {"status": "success", "message": "Moto creada para auditoría", "moto_id": moto.id}
    except Exception as e:
        return {"status": "error", "message": str(e)}
