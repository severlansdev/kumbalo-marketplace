from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel
import random
from datetime import datetime, timedelta

router = APIRouter()

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
    embargos: bool

# Base de datos mock de modelos comunes para generar reportes creíbles
MARCAS = ["YAMAHA", "HONDA", "SUZUKI", "KAWASAKI", "DUCATI", "BMW", "KTM", "ROYAL ENFIELD"]
LINEAS = ["MT-09", "CBR-600", "GSX-R", "NINJA", "PANIGALE", "GS-1250", "DUKE-390", "HIMALAYAN"]
COLORES = ["NEGRO", "ROJO", "AZUL", "BLANCO", "VERDE", "GRIS", "AMARILLO"]

@router.get("/consulta/{placa}", response_model=RuntResponse)
async def consultar_placa(
    placa: str = Path(..., description="Placa del vehículo Ej: ABC12D", min_length=5, max_length=6)
):
    """
    Simula una consulta al RUNT / SIMIT público para extraer el estado del vehículo.
    Este endpoint es un Lead Magnet para que los usuarios verifiquen el estado antes de comprar.
    """
    placa = placa.upper().replace("-", "")
    
    # Validar formato de placa (3 letras + 2/3 números o letras)
    if len(placa) < 5 or len(placa) > 6:
        raise HTTPException(status_code=400, detail="Formato de placa inválido. Usa AAA123 o ABC12D.")

    # Simular una pequeña latencia externa (opcional, para la animación de frontend)
    # await asyncio.sleep(1)

    # Generación procedimental controlada por el texto de la placa (Semilla)
    seed = sum([ord(c) for c in placa])
    random.seed(seed)

    marca = random.choice(MARCAS)
    linea = random.choice(LINEAS)
    modelo = random.randint(2010, 2024)
    color = random.choice(COLORES)
    
    # Logica de estados
    soat_dias = random.randint(-50, 300)
    rtm_dias = random.randint(-50, 300)
    
    hoy = datetime.now()
    vencimiento_soat = hoy + timedelta(days=soat_dias)
    vencimiento_rtm = hoy + timedelta(days=rtm_dias)
    
    estado_soat = "VIGENTE" if soat_dias > 0 else "VENCIDO"
    estado_rtm = "VIGENTE" if rtm_dias > 0 else "VENCIDA"
    
    multas = random.choice([0, 0, 0, 1, 2, 5]) 
    embargos = random.choice([False, False, False, False, True])

    # Si es una placa del año, RTM no aplica y es vigente automático
    if modelo >= 2023:
        estado_rtm = "VIGENTE"
        vencimiento_rtm = datetime(modelo + 2, 1, 1)

    return RuntResponse(
        placa=placa,
        marca=marca,
        linea=linea,
        modelo=modelo,
        color=color,
        estado_soat=estado_soat,
        vencimiento_soat=vencimiento_soat.strftime("%Y-%m-%d"),
        estado_rtm=estado_rtm,
        vencimiento_rtm=vencimiento_rtm.strftime("%Y-%m-%d"),
        multas=multas,
        embargos=embargos
    )
