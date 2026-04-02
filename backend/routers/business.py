from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from .. import models
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/business", tags=["business", "monetization"])

# SCHEMAS
class CreditoCreate(BaseModel):
    moto_id: int
    monto_solicitado: float
    plazo_meses: int
    ingresos_mensuales: float
    entidad: str = "Bancolombia Sufi"

class SeguroCreate(BaseModel):
    moto_id: int
    tipo_seguro: str
    aseguradora: str = "SURA"

class SubastaCreate(BaseModel):
    moto_id: int
    precio_minimo: float
    duracion_horas: int = 24


# 1. Financiamiento BaaS
@router.post("/creditos/solicitar")
def solicitar_credito(req: CreditoCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Crea un lead de crédito para Bancolombia Sufi"""
    moto = db.query(models.Moto).filter(models.Moto.id == req.moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada para financiar")

    nuevo_credito = models.LeadCredito(
        moto_id=req.moto_id,
        usuario_id=current_user.id,
        monto_solicitado=req.monto_solicitado,
        plazo_meses=req.plazo_meses,
        ingresos_mensuales=req.ingresos_mensuales,
        entidad_financiera=req.entidad
    )
    db.add(nuevo_credito)
    db.commit()
    db.refresh(nuevo_credito)
    
    # En un entorno real, aquí se dispara un Webhook a la API del Banco.
    return {"status": "success", "message": "Solicitud de crédito enviada a pre-aprobación.", "lead_id": nuevo_credito.id}


# 2. Seguros Embebidos
@router.post("/seguros/cotizar")
def cotizar_seguro(req: SeguroCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Crea un lead de seguro Todo Riesgo"""
    moto = db.query(models.Moto).filter(models.Moto.id == req.moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada para asegurar")

    nuevo_seguro = models.LeadSeguro(
        moto_id=req.moto_id,
        usuario_id=current_user.id,
        tipo_seguro=req.tipo_seguro,
        aseguradora=req.aseguradora
    )
    db.add(nuevo_seguro)
    db.commit()
    db.refresh(nuevo_seguro)
    
    return {"status": "success", "message": "Cotización de seguro en proceso.", "lead_id": nuevo_seguro.id}


# 3. Subastas C2B para Concesionarios
@router.post("/subastas/crear")
def crear_subasta(req: SubastaCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Crea una subasta visible solo para concesionarios"""
    moto = db.query(models.Moto).filter(models.Moto.id == req.moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")
    if moto.propietario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres el propietario de esta moto.")

    fecha_fin = datetime.now() + timedelta(hours=req.duracion_horas)
    
    nueva_subasta = models.SubastaMoto(
        moto_id=req.moto_id,
        vendedor_id=current_user.id,
        precio_minimo=req.precio_minimo,
        fecha_fin=fecha_fin
    )
    db.add(nueva_subasta)
    db.commit()
    db.refresh(nueva_subasta)
    
    return {"status": "success", "message": f"Subasta iniciada. Finaliza en {req.duracion_horas} horas.", "subasta_id": nueva_subasta.id}
