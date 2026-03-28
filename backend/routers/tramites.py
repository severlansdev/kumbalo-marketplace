from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/tramites", tags=["trámites"])

@router.post("/solicitar")
async def solicitar_tramite(
    moto_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Crea una solicitud de Traspaso Express para una moto específica"""
    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
    
    if not moto:
        raise HTTPException(status_code=404, detail="Motocicleta no encontrada")
        
    # Verificar si ya existe un trámite activo para esta moto
    tramite_previo = db.query(models.Tramite).filter(models.Tramite.moto_id == moto_id).first()
    if tramite_previo and tramite_previo.estado != "finalizado":
        raise HTTPException(status_code=400, detail="Ya existe un trámite en curso para esta motocicleta")

    nuevo_tramite = models.Tramite(
        moto_id=moto.id,
        vendedor_id=moto.propietario_id,
        comprador_id=current_user.id,
        tipo="traspaso_express",
        estado="solicitado"
    )
    
    db.add(nuevo_tramite)
    db.commit()
    db.refresh(nuevo_tramite)
    
    return {
        "status": "success",
        "message": "Trámite solicitado exitosamente. Un gestor Kumbalo se pondrá en contacto pronto.",
        "tramite_id": nuevo_tramite.id
    }

@router.get("/mis-tramites")
async def get_mis_tramites(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    """Obtiene la lista de trámites donde el usuario es comprador o vendedor"""
    tramites = db.query(models.Tramite).filter(
        (models.Tramite.comprador_id == current_user.id) | 
        (models.Tramite.vendedor_id == current_user.id)
    ).all()
    
    return tramites
