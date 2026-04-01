from fastapi import APIRouter, HTTPException, Path, Query, Request, Depends
from pydantic import BaseModel
from typing import Optional
import os
from sqlalchemy.orm import Session
from ..utils.vehicle_agent import VehicleIntelligenceAgent
from ..limiter import limiter
from ..database import get_db
from .. import models
try:
    from .payments import sdk
except ImportError:
    import mercadopago
    sdk = mercadopago.SDK(os.getenv("MERCADOPAGO_ACCESS_TOKEN", "fallback"))

router = APIRouter()
agent = VehicleIntelligenceAgent()

class RuntResponse(BaseModel):
    placa: str
    marca: str
    linea: str
    modelo: int
    color: str
    estado_soat: str
    vencimiento_soat: str
    estado_rtm: str
    vencimiento_rtm: str
    multas: int
    valor_multas: float
    embargos: bool
    limitaciones_propiedad: str
    es_verificado: bool = False
    fuente: str = "IA KUMBALO"

class ReportPurchaseRequest(BaseModel):
    placa: str
    email: str
    metodo_pago: str = "mercadopago"

@router.get("/get-captcha")
@limiter.limit("10/minute")
async def get_runt_captcha(request: Request):
    """Obtiene un captcha fresco del RUNT para resolver en el frontend."""
    return await agent.runt.get_captcha()

@router.get("/consulta/{placa}", response_model=RuntResponse)
@limiter.limit("5/minute")
async def consultar_placa(
    request: Request,
    placa: str = Path(..., description="Placa del vehículo Ej: ABC12D", min_length=5, max_length=6),
    vin: Optional[str] = Query(None, description="VIN (Serial de chasis)"),
    doc_type: Optional[str] = Query(None, description="Tipo de documento (C, E, N, P)"),
    doc_num: Optional[str] = Query(None, description="Número de documento"),
    captcha_token: Optional[str] = Query(None, description="ID del captcha"),
    captcha_value: Optional[str] = Query(None, description="Valor resuelto por el usuario")
):
    """
    Consulta dinámica y determinista del ADN vehicular.
    Soporta resolución de Captcha HITL para datos 100% reales.
    """
    try:
        dna = await agent.get_vehicle_dna(placa, vin, doc_type, doc_num, captcha_token, captcha_value)
        return dna
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta vehicular: {str(e)}")

@router.post("/comprar-reporte")
async def comprar_reporte_completo(request_data: ReportPurchaseRequest, db: Session = Depends(get_db)):
    """
    Genera una intención de compra para el Reporte de Tradición RUNT Completo.
    Kumbalo cobra $40,000 (Costo RUNT $36,000 + $4,000 Comisión).
    """
    try:
        frontend_url = os.getenv("FRONTEND_URL", "https://kumbalo-marketplace.vercel.app")
        
        # Datos de la preferencia de MercadoPago
        preference_data = {
            "items": [
                {
                    "title": f"Reporte RUNT Tradición: {request_data.placa}",
                    "quantity": 1,
                    "unit_price": 40000.0,
                    "currency_id": "COP"
                }
            ],
            "payer": {
                "email": request_data.email
            },
            "back_urls": {
                "success": f"{frontend_url}/dashboard.html?report_payment=success&placa={request_data.placa}",
                "failure": f"{frontend_url}/dashboard.html?report_payment=failure",
                "pending": f"{frontend_url}/dashboard.html?report_payment=pending"
            },
            "auto_return": "approved",
            "external_reference": f"runt_{request_data.placa}",
            "notification_url": f"{os.getenv('BACKEND_URL', 'https://kumbalo-api.vercel.app')}/api/payments/webhook"
        }

        preference_response = sdk.preference().create(preference_data)
        
        if preference_response["status"] not in [200, 201]:
            raise HTTPException(status_code=400, detail="Error al conectar con MercadoPago")
            
        preference = preference_response["response"]

        return {
            "status": "success",
            "message": f"Preferencia de pago generada para la placa {request_data.placa}",
            "monto": 40000,
            "currency": "COP",
            "init_point": preference["init_point"],
            "preference_id": preference["id"]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la compra: {str(e)}")

