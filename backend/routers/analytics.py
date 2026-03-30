from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import random
from datetime import datetime, timedelta
from .. import models, schemas
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix="/analytics", tags=["Market Intelligence"])

# Simulación de tendencia de mercado por marcas comunes en Colombia
MARKET_TRENDS = {
    "Yamaha": {"trend": 0.05, "demand": "High", "reason": "Escasez de repuestos importados"},
    "Honda": {"trend": 0.02, "demand": "Medium", "reason": "Lanzamiento de nuevos modelos 2025"},
    "Suzuki": {"trend": -0.01, "demand": "Stable", "reason": "Ajuste de inventario nacional"},
    "Ducati": {"trend": 0.08, "demand": "High", "reason": "Crecimiento de nicho de lujo"},
    "BMW": {"trend": 0.03, "demand": "High", "reason": "Temporada de viajes Adventure"},
    "Kawasaki": {"trend": 0.04, "demand": "Medium", "reason": "Dólar estable favorece importación"},
}

@router.get("/predictive-alerts")
async def get_predictive_alerts(current_user: models.Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Simula la ejecución del Agente de Datos (/data_ml) para generar alertas predictivas personalizadas.
    Analiza la moto del usuario y la tendencia actual del mercado.
    """
    # Buscamos la moto más reciente del usuario para darle relevancia
    user_moto = db.query(models.Moto).filter(models.Moto.propietario_id == current_user.id).order_by(models.Moto.id.desc()).first()
    
    alerts = []
    
    if user_moto:
        brand = user_moto.marca
        trend_info = MARKET_TRENDS.get(brand, {"trend": random.uniform(-0.02, 0.04), "demand": "Stable", "reason": "Fluctuación normal"})
        
        percent_change = trend_info["trend"] * 100
        
        if percent_change > 0:
            alerts.append({
                "type": "opportunity",
                "title": f"🚀 ¡Momento de Venta Ideal!",
                "message": f"Tu {brand} {user_moto.modelo} ha subido un {percent_change:.1f}% en el mercado este mes. {trend_info['reason']}. ¿Quieres aprovechar para cambiarla?",
                "agent": "data_ml",
                "cta": "Vender ahora",
                "priority": "High"
            })
        else:
            alerts.append({
                "type": "info",
                "title": "💡 Tip de Mantenimiento",
                "message": f"El valor de las {brand} se mantiene estable. Es un buen momento para realizar mantenimiento preventivo y conservar su precio de reventa.",
                "agent": "customer_success",
                "cta": "Agendar Taller",
                "priority": "Medium"
            })
    else:
        # Alerta general si no tiene moto
        alerts.append({
            "type": "buying_opportunity",
            "title": "🔍 Oportunidad de Compra",
            "message": "Las motos Ducati y BMW premium han bajado ligeramente su tiempo de venta. Es un gran momento para negociar tu próxima máquina.",
            "agent": "data_ml",
            "cta": "Ver Catálogo",
            "priority": "Medium"
        })

    return alerts

@router.get("/market-pulse")
async def get_market_pulse():
    """Retorna el 'Pulso del Mercado' general para el dashboard."""
    pulse_data = []
    for brand, data in MARKET_TRENDS.items():
        pulse_data.append({
            "brand": brand,
            "change": f"{data['trend']*100:+.1f}%",
            "demand": data["demand"],
            "status": "up" if data["trend"] > 0 else "down"
        })
    return pulse_data
