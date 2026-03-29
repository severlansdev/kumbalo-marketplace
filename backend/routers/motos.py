"""
Router de Motos - Catálogo, creación y gestión de publicaciones.
Gestiona la lógica de subida de imágenes a S3 y el cálculo de comisiones.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from typing import List, Optional
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
    marca: Optional[str] = None, 
    anio: Optional[int] = None, 
    precio_max: Optional[float] = None, 
    db: Session = Depends(get_db)
) -> List[models.Moto]:
    """
    Obtiene el catálogo público de motos con filtros opcionales.
    
    Args:
        skip: Número de registros a saltar.
        limit: Límite de registros a retornar.
        marca: Filtro por marca (parcial/ilike).
        anio: Filtro por año exacto.
        precio_max: Filtro por precio máximo.
    """
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
    kilometraje: int = Form(0),
    cilindraje: Optional[int] = Form(None),
    color: Optional[str] = Form(None),
    transmision: Optional[str] = Form(None),
    combustible: Optional[str] = Form(None),
    ciudad: Optional[str] = Form(None),
    descripcion: str = Form("Sin descripción"),
    fotos: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(get_current_user)
):
    # 1. Crear la instancia de la moto primero para tener su ID
    nueva_moto = models.Moto(
        marca=sanitize_input(marca),
        modelo=sanitize_input(modelo),
        año=año,
        precio=precio,
        kilometraje=kilometraje,
        cilindraje=cilindraje,
        color=sanitize_input(color) if color else None,
        transmision=sanitize_input(transmision) if transmision else None,
        combustible=sanitize_input(combustible) if combustible else None,
        ciudad=sanitize_input(ciudad) if ciudad else None,
        descripcion=sanitize_input(descripcion),
        propietario_id=current_user.id,
        commission_fee=calculate_kumbalo_fee(precio),
        commission_type="fixed",
        estado="activa"
    )
    
    db.add(nueva_moto)
    db.commit()
    db.refresh(nueva_moto)

    # 2. Procesar y subir todas las fotos
    urls_subidas = []
    for i, foto in enumerate(fotos):
        try:
            image_url = upload_image_to_s3(foto.file, foto.filename, foto.content_type)
            urls_subidas.append(image_url)
            
            # Crear registro en moto_imagenes
            nueva_imagen = models.MotoImagen(
                moto_id=nueva_moto.id,
                url=image_url,
                orden=i,
                es_principal=(i == 0)
            )
            db.add(nueva_imagen)
        except Exception as e:
            print(f"Error subiendo foto {i}: {e}")
            continue # Intentar con las siguientes si una falla

    # 3. Actualizar la imagen principal en el modelo Moto (para compatibilidad)
    if urls_subidas:
        nueva_moto.image_url = urls_subidas[0]
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
