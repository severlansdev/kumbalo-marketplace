from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel
from typing import Optional
from ..utils.vehicle_agent import VehicleIntelligenceAgent

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

@router.get("/consulta/{placa}", response_model=RuntResponse)
async def consultar_placa(
    placa: str = Path(..., description="Placa del vehículo Ej: ABC12D", min_length=5, max_length=6),
    vin: Optional[str] = Query(None, description="VIN (Serial de chasis) para consulta verificada")
):
    """
    Consulta dinámica y determinista del ADN vehicular.
    Si se proporciona el VIN, se simula una consulta verificada al RUNT.
    """
    try:
        dna = agent.get_vehicle_dna(placa, vin)
        return dna
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta vehicular: {str(e)}")

@router.post("/comprar-reporte")
async def comprar_reporte_completo(request: ReportPurchaseRequest):
    """
    Genera una intención de compra para el Reporte de Tradición RUNT Completo.
    Kumbalo cobra $40,000 (Costo RUNT $36,000 + $4,000 Comisión).
    """
    try:
        # Aquí se integraría con el router de payments para generar la preferencia de MercadoPago
        return {
            "status": "success",
            "message": f"Preferencia de pago generada para la placa {request.placa}",
            "monto": 40000,
            "currency": "COP",
            "init_point": f"https://www.mercadopago.com.co/checkout/v1/redirect?pref_id=KUMBALO-RUNT-{request.placa}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar la compra: {str(e)}")

