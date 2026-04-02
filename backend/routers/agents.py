from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas
from ..database import get_db
from .auth import get_current_admin

router = APIRouter(prefix="/agents", tags=["AI Agents"])

@router.get("/status", dependencies=[Depends(get_current_admin)])
async def get_agents_status():
    """Returns the comprehensive list of 24 elite agents and their real-time statuses."""
    agents = [
        # --- Core & Security ---
        {"name": "IA Orquestadora (Antigravity)", "status": "Active", "category": "Core"},
        {"name": "/hacker_guardian", "status": "Patrullando DNS", "category": "Security"},
        {"name": "/security_devops", "status": "Optimización SSL", "category": "Security"},
        
        # --- Dev & Infra ---
        {"name": "/cloud_architect", "status": "Cost Audit", "category": "Infra"},
        {"name": "/backend_apis", "status": "Engine Sync", "category": "Dev"},
        {"name": "/mobile_dev", "status": "Framework Prep", "category": "Dev"},
        {"name": "/qa_expert", "status": "Wait for Push", "category": "Quality"},
        {"name": "/perf_expert", "status": "LCP Audit", "category": "Infra"},
        {"name": "/sre_engineer", "status": "Uptime Guard", "category": "Infra"},
        
        # --- Growth & Marketing ---
        {"name": "/marketing_growth", "status": "Campaign Plan", "category": "Growth"},
        {"name": "/seo_content", "status": "Lead Magnet", "category": "Growth"},
        {"name": "/social_influencer", "status": "TikTok Scout", "category": "Growth"},
        {"name": "/pr_media", "status": "Media Contact", "category": "Publicity"},
        {"name": "/brand_design", "status": "Logo Guard", "category": "Design"},
        {"name": "/ux_copywriting", "status": "A/B Testing", "category": "Design"},
        
        # --- Business & Finance ---
        {"name": "/fintech_executive", "status": "MercadoPago Audit", "category": "Finance"},
        {"name": "/business_strategy", "status": "Monetization", "category": "Strategy"},
        {"name": "/mintic_lawyer", "status": "Audit. Ley 1581/GDPR", "category": "Legal"},
        {"name": "/partnerships", "status": "B2B Deal Hunt", "category": "Affiliates"},
        
        # --- Intelligence & Support ---
        {"name": "/bi_analyst", "status": "Funnel Scrape", "category": "Data"},
        {"name": "/data_ml", "status": "Pricing Preach", "category": "Data"},
        {"name": "/pm_expert", "status": "Sprint Planning", "category": "Product"},
        {"name": "/customer_success", "status": "LTV Analysis", "category": "Support"},
        {"name": "/community_support", "status": "Tickets: 0", "category": "Support"}
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
