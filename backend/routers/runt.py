from fastapi import APIRouter, HTTPException, Path
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

@router.get("/consulta/{placa}", response_model=RuntResponse)
async def consultar_placa(
    placa: str = Path(..., description="Placa del vehículo Ej: ABC12D", min_length=5, max_length=6)
):
    """
    Consulta dinámica y determinista del ADN vehicular.
    Utiliza el VehicleIntelligenceAgent para garantizar datos estables sin costo de API externo.
    """
    try:
        dna = agent.get_vehicle_dna(placa)
        return dna
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en la consulta vehicular: {str(e)}")

