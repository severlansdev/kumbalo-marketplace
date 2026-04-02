from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel

from .. import models
from ..database import get_db
from .auth import get_current_user
from ..utils import email_agent

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


class PujaCreate(BaseModel):
    monto: float

@router.get("/subastas/activas")
def listar_subastas(db: Session = Depends(get_db)):
    """Retorna las subastas activas (para visualización del Concesionario)"""
    # Solo traemos activas y en tiempo
    subastas = db.query(models.SubastaMoto).filter(
        models.SubastaMoto.estado == "activa",
        models.SubastaMoto.fecha_fin > datetime.now()
    ).all()
    
    resultados = []
    for s in subastas:
        resultados.append({
            "id": s.id,
            "moto": f"{s.moto.marca} {s.moto.modelo} ({s.moto.año})",
            "moto_id": s.moto_id,
            "precio_minimo": s.precio_minimo,
            "mejor_oferta": s.mejor_oferta,
            "fecha_fin": s.fecha_fin,
            "image_url": s.moto.image_url
        })
    return resultados


@router.post("/subastas/{subasta_id}/pujar")
def realizar_puja(subasta_id: int, req: PujaCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Permite enviar una puja a una subasta específica"""
    subasta = db.query(models.SubastaMoto).filter(models.SubastaMoto.id == subasta_id).first()
    if not subasta:
        raise HTTPException(status_code=404, detail="Subasta no encontrada")
    
    if subasta.estado != "activa" or subasta.fecha_fin < datetime.now():
        raise HTTPException(status_code=400, detail="Esta subasta ha cerrado")
        
    if current_user.id == subasta.vendedor_id:
        raise HTTPException(status_code=400, detail="No puedes pujar por tu propia moto")
        
    if req.monto <= subasta.mejor_oferta:
        raise HTTPException(status_code=400, detail=f"La puja debe ser mayor a la mejor oferta actual (${subasta.mejor_oferta})")

    # Anti-Sniping Protection (Añade 2 min si quedan menos de 2 min)
    if (subasta.fecha_fin - datetime.now()).total_seconds() < 120:
        subasta.fecha_fin = subasta.fecha_fin + timedelta(minutes=2)

    # Registrar Puja
    nueva_puja = models.HistorialPuja(
        subasta_id=subasta_id,
        postor_id=current_user.id,
        monto=req.monto
    )
    db.add(nueva_puja)
    
    # Actualizar Subasta
    subasta.mejor_oferta = req.monto
    subasta.concesionario_ganador_id = current_user.id
    
    db.commit()
    
    # Notificación Transaccional
    email_agent.notify_nueva_puja(
        vendedor_email=subasta.vendedor.email,
        marca=f"{subasta.moto.marca} {subasta.moto.modelo}",
        monto=req.monto
    )
    
    return {"status": "success", "message": "Puja registrada exitosamente", "nueva_oferta": subasta.mejor_oferta, "fecha_fin": subasta.fecha_fin}

# ==========================================
# 4. Smart Trade-Ins (Permutas C2C)
# ==========================================

class PermutaCreate(BaseModel):
    moto_ofrecida_id: int
    moto_objetivo_id: int
    excedente: float

@router.post("/permutas/ofrecer")
def ofrecer_permuta(req: PermutaCreate, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Crea una oferta de permuta (Trade-In) + Dinero desde un usuario a otro."""
    moto_objetivo = db.query(models.Moto).filter(models.Moto.id == req.moto_objetivo_id).first()
    moto_ofrecida = db.query(models.Moto).filter(models.Moto.id == req.moto_ofrecida_id).first()
    
    if not moto_objetivo or not moto_ofrecida:
        raise HTTPException(status_code=404, detail="Alguna de las motos no existe.")
        
    if moto_ofrecida.propietario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No eres dueño de la moto que estás ofreciendo como canje.")
        
    if moto_objetivo.propietario_id == current_user.id:
        raise HTTPException(status_code=400, detail="No puedes permutar contigo mismo.")

    nueva_permuta = models.OfertaPermuta(
        oferente_id=current_user.id,
        receptor_id=moto_objetivo.propietario_id,
        moto_ofrecida_id=req.moto_ofrecida_id,
        moto_objetivo_id=req.moto_objetivo_id,
        excedente=req.excedente
    )
    db.add(nueva_permuta)
    db.commit()
    db.refresh(nueva_permuta)
    
    return {"status": "success", "message": "Oferta de permuta enviada. Notificaremos al vendedor.", "permuta_id": nueva_permuta.id}


@router.get("/permutas/mis-ofertas")
def listar_permutas(db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Retorna las ofertas de permuta Recibidas y Emitidas"""
    recibidas = db.query(models.OfertaPermuta).filter(models.OfertaPermuta.receptor_id == current_user.id).all()
    emitidas = db.query(models.OfertaPermuta).filter(models.OfertaPermuta.oferente_id == current_user.id).all()
    
    def parse_permuta(p):
        return {
            "id": p.id,
            "estado": p.estado,
            "excedente": p.excedente,
            "moto_ofrecida": f"{p.moto_ofrecida.marca} {p.moto_ofrecida.modelo}",
            "moto_objetivo": f"{p.moto_objetivo.marca} {p.moto_objetivo.modelo}",
            "fecha": p.created_at
        }
        
    return {
        "recibidas": [parse_permuta(p) for p in recibidas],
        "emitidas": [parse_permuta(p) for p in emitidas]
    }


@router.post("/permutas/{permuta_id}/responder")
def responder_permuta(permuta_id: int, accion: str, db: Session = Depends(get_db), current_user: models.Usuario = Depends(get_current_user)):
    """Permite al receptor Aceptar o Rechazar la permuta. Si acepta, se genera Double Escrow."""
    permuta = db.query(models.OfertaPermuta).filter(models.OfertaPermuta.id == permuta_id).first()
    if not permuta:
        raise HTTPException(status_code=404, detail="Permuta no encontrada")
        
    if permuta.receptor_id != current_user.id:
        raise HTTPException(status_code=403, detail="No puedes responder a una oferta que no es tuya.")
        
    if accion not in ["aceptar", "rechazar"]:
        raise HTTPException(status_code=400, detail="Acción inválida. Usa 'aceptar' o 'rechazar'.")
        
    if accion == "rechazar":
        permuta.estado = "rechazada"
        db.commit()
        email_agent.notify_estado_permuta(
            receptor_email=permuta.oferente.email,
            moto_ofrecida=f"{permuta.moto_ofrecida.marca} {permuta.moto_ofrecida.modelo}",
            moto_objetivo=f"{permuta.moto_objetivo.marca} {permuta.moto_objetivo.modelo}",
            estado="rechazada"
        )
        return {"status": "success", "message": "Oferta rechazada."}
        
    if accion == "aceptar":
        permuta.estado = "aceptada"
        # Aquí se inicia el Double Escrow
        db.commit()
        email_agent.notify_estado_permuta(
            receptor_email=permuta.oferente.email,
            moto_ofrecida=f"{permuta.moto_ofrecida.marca} {permuta.moto_ofrecida.modelo}",
            moto_objetivo=f"{permuta.moto_objetivo.marca} {permuta.moto_objetivo.modelo}",
            estado="aceptada"
        )
        return {"status": "success", "message": "¡Oferta Aceptada! Iniciando Traspaso Dual."}
