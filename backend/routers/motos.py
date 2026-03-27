from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
from .. import schemas, models
from ..database import get_db
from .auth import get_current_user, get_current_admin
from ..aws_s3 import upload_image_to_s3
from ..utils import sanitize_input
from ..utils.fees import calculate_kumbalo_fee

router = APIRouter(prefix="/motos", tags=["motos"])

@router.get("/", response_model=List[schemas.MotoResponse])
def get_motos(
    skip: int = 0, 
    limit: int = 100, 
    marca: str = None, 
    anio: int = None, 
    precio_max: float = None, 
    db: Session = Depends(get_db)
):
    query = db.query(models.Moto)
    if marca:
        query = query.filter(models.Moto.marca.ilike(f"%{sanitize_input(marca)}%"))
    if anio:
        query = query.filter(models.Moto.año == anio)
    if precio_max:
        query = query.filter(models.Moto.precio <= precio_max)
        
    motos = query.order_by(models.Moto.created_at.desc()).offset(skip).limit(limit).all()
    return motos

@router.get("/{moto_id}", response_model=schemas.MotoResponse)
def get_moto(moto_id: int, db: Session = Depends(get_db)):
    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")
    return moto

@router.post("/", response_model=schemas.MotoResponse)
async def create_moto(
    marca: str = Form(...),
    modelo: str = Form(...),
    año: int = Form(...),
    precio: float = Form(...),
    kilometraje: int = Form(...),
    descripcion: str = Form(...),
    foto: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    try:
        # Subir foto directo a AWS S3
        image_url = upload_image_to_s3(foto.file, foto.filename, foto.content_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subiendo imagen a AWS S3: {str(e)}")

    nueva_moto = models.Moto(
        marca=sanitize_input(marca),
        modelo=sanitize_input(modelo),
        año=año,
        precio=precio,
        kilometraje=kilometraje,
        descripcion=sanitize_input(descripcion),
        image_url=image_url,
        propietario_id=current_user.id,
        commission_fee=calculate_kumbalo_fee(precio),
        commission_type="fixed"
    )
    
    db.add(nueva_moto)
    db.commit()
    db.refresh(nueva_moto)
    return nueva_moto

@router.get("/mis-motos", response_model=List[schemas.MotoResponse])
def get_mis_motos(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    # Trae exclusivamente las motos del usuario en sesion (Dashboard)
    return db.query(models.Moto).filter(models.Moto.propietario_id == current_user.id).order_by(models.Moto.created_at.desc()).all()

@router.post("/{moto_id}/favorito")
def toggle_favorito(moto_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")
    
    # Check if exists
    fav = db.query(models.Favorito).filter(models.Favorito.usuario_id == current_user.id, models.Favorito.moto_id == moto_id).first()
    
    if fav:
        db.delete(fav)
        db.commit()
        return {"status": "removed"}
    else:
        nuevo_fav = models.Favorito(usuario_id=current_user.id, moto_id=moto_id)
        db.add(nuevo_fav)
        db.commit()
        return {"status": "added"}

@router.get("/list/favoritas", response_model=List[schemas.MotoResponse])
def get_favoritas(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    favoritos = db.query(models.Favorito).filter(models.Favorito.usuario_id == current_user.id).all()
    moto_ids = [fav.moto_id for fav in favoritos]
    if not moto_ids:
        return []
    motos = db.query(models.Moto).filter(models.Moto.id.in_(moto_ids)).order_by(models.Moto.created_at.desc()).all()
    return motos

@router.delete("/{moto_id}")
def delete_moto_admin(moto_id: int, db: Session = Depends(get_db), current_admin: models.Usuario = Depends(get_current_admin)):
    moto = db.query(models.Moto).filter(models.Moto.id == moto_id).first()
    if not moto:
        raise HTTPException(status_code=404, detail="Moto no encontrada")
    
    db.delete(moto)
    db.commit()
    return {"status": "Moto eliminada exitosamente (Acción de Administrador)"}
