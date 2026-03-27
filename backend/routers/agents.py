from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .auth import get_current_admin

router = APIRouter(prefix="/agents", tags=["AI Agents"])

@router.get("/status", dependencies=[Depends(get_current_admin)])
async def get_agents_status():
    """Returns the list of 17 agents + Arquitekto Elite and their mock status."""
    agents = [
        {"name": "Agente de Seguridad & DevOps", "status": "Online", "category": "Infra"},
        {"name": "Agente de Backend & APIs", "status": "Online", "category": "Dev"},
        {"name": "Agente de UX/UI & Copywriting", "status": "Online", "category": "Design"},
        {"name": "Agente de Marketing & Growth", "status": "Online", "category": "Growth"},
        {"name": "Agente de PMP & Gestión de Proyectos", "status": "Online", "category": "Management"},
        {"name": "Agente de QA & Diseño Web", "status": "Online", "category": "Dev"},
        {"name": "Agente de SEO & Contenido", "status": "Online", "category": "Growth"},
        {"name": "Agente de Business Strategy", "status": "Online", "category": "Management"},
        {"name": "Agente de Legal & Compliance", "status": "Legal", "category": "Compliance"},
        {"name": "Agente de SRE Engineer", "status": "Online", "category": "Infra"},
        {"name": "Agente de BI Analyst", "status": "Online", "category": "Data"},
        {"name": "Agente de Data & Machine Learning", "status": "Online", "category": "Data"},
        {"name": "Agente de Fintech & Visión de Negocio", "status": "Online", "category": "Finance"},
        {"name": "Agente de Alianzas & Ecosistema", "status": "Online", "category": "Partners"},
        {"name": "Agente de Comunidad & Soporte", "status": "Online", "category": "Support"},
        {"name": "Agente de Performance Expert", "status": "Online", "category": "Infra"},
        {"name": "Agente de Diseño Gráfico & Brand", "status": "Online", "category": "Design"},
        {"name": "Arquitekto Elite (Super-Agente 18)", "status": "Active", "category": "Core"}
    ]
    return agents

@router.post("/command", dependencies=[Depends(get_current_admin)])
async def send_command(command: str, db: Session = Depends(get_db)):
    """Sends a direct command to the Arquitekto Elite."""
    new_task = models.BacklogAgente(
        peticion=command,
        agente_asignado="Arquitekto Elite",
        prioridad=3 # High priority for direct admin commands
    )
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return {"message": "Comando recibido y delegado al Arquitekto Elite", "task_id": new_task.id}

@router.get("/audit-logs", dependencies=[Depends(get_current_admin)])
async def get_audit_logs(db: Session = Depends(get_db)):
    """Returns the history of agent audits/actions."""
    # This usually pulls from a more detailed log, but for now we use the TelegramHistory or Backlog
    tasks = db.query(models.BacklogAgente).order_by(models.BacklogAgente.created_at.desc()).limit(10).all()
    return tasks
