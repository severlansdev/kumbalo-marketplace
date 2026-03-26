from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from .. import schemas, models
from ..database import get_db
from .auth import get_current_user
from ..email_utils import send_email

router = APIRouter(prefix="/mensajes", tags=["mensajes"])

from .chat import manager
import asyncio

@router.post("/", response_model=schemas.MensajeResponse)
async def crear_mensaje(mensaje: schemas.MensajeCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    # Check that recipient exists
    destinatario = db.query(models.Usuario).filter(models.Usuario.id == mensaje.destinatario_id).first()
    if not destinatario:
        raise HTTPException(status_code=404, detail="Usuario destinatario no encontrado")
        
    nuevo_mensaje = models.Mensaje(
        remitente_id=current_user.id,
        destinatario_id=mensaje.destinatario_id,
        moto_id=mensaje.moto_id,
        contenido=mensaje.contenido
    )
    
    db.add(nuevo_mensaje)
    db.commit()
    db.refresh(nuevo_mensaje)
    
    # Broadcast to WebSocket if user is online
    ws_payload = {
        "type": "new_message",
        "data": {
            "id": nuevo_mensaje.id,
            "remitente_id": nuevo_mensaje.remitente_id,
            "moto_id": nuevo_mensaje.moto_id,
            "contenido": nuevo_mensaje.contenido
        }
    }
    await manager.send_personal_message(ws_payload, destinatario.id)

    # Notificar al vendedor por correo
    send_email(
        to_email=destinatario.email,
        subject="¡Tienes un nuevo mensaje en KUMBALO!",
        body=f"Hola {destinatario.nombre}, recibiste un mensaje sobre tu publicación. Entra a tu Dashboard para responder."
    )
    
    return nuevo_mensaje

@router.get("/me", response_model=List[schemas.MensajeResponse])
def mis_mensajes_recibidos(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    mensajes = db.query(models.Mensaje).filter(models.Mensaje.destinatario_id == current_user.id).order_by(models.Mensaje.created_at.desc()).all()
    return mensajes

@router.put("/{mensaje_id}/leido")
def marcar_como_leido(mensaje_id: int, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    mensaje = db.query(models.Mensaje).filter(models.Mensaje.id == mensaje_id).first()
    if not mensaje:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    if mensaje.destinatario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")
        
    mensaje.leido = True
    db.commit()
    return {"status": "leido"}
