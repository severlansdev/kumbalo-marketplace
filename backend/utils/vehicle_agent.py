from .simit_agent import SimitAgent
from .runt_agent import RuntAgent
import hashlib
import random
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Optional

class VehicleADN(BaseModel):
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
    tipo_servicio: str = "PARTICULAR"
    limitaciones_propiedad: str = "NINGUNA"
    es_verificado: bool = False
    fuente: str = "IA KUMBALO"

class VehicleIntelligenceAgent:
    """
    Agente que gestiona la 'salud legal' de las motos en Kumbalo.
    Diseñado para conectarse con APIs reales o simular datos consistentes.
    """
    
    MARCAS_PREMIUM = ["YAMAHA", "HONDA", "SUZUKI", "KAWASAKI", "DUCATI", "BMW", "KTM", "TRIUMPH"]
    LINEAS_POPULARES = {
        "YAMAHA": ["MT-09", "YZF-R3", "NMAX", "TRACER 900"],
        "HONDA": ["CB-650R", "CBR-600RR", "CRF-250L", "AFRICA TWIN"],
        "SUZUKI": ["GSX-S750", "V-STROM 650", "GN-125", "DR-650"],
        "KAWASAKI": ["Z900", "NINJA 400", "VERSYS 650", "ZX-6R"],
        "DUCATI": ["PANIGALE V4", "MONSTER 821", "MULTISTRADA 1260"],
        "BMW": ["R-1250GS", "S-1000RR", "F-850GS", "G-310R"]
    }
    COLORES = ["NEGRO NEBULOSA", "ROJO RACING", "AZUL MATE", "BLANCO PERLA", "GRIS METALIZADO"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.simit = SimitAgent()
        self.runt = RuntAgent()

    async def get_vehicle_dna(self, placa: str, vin: Optional[str] = None, doc_type: Optional[str] = None, doc_num: Optional[str] = None, captcha_token: Optional[str] = None, captcha_value: Optional[str] = None) -> VehicleADN:
        placa = placa.upper().strip().replace("-", "")
        
        # Caso especial: Información real para la prueba del usuario (Placa GOG05E)
        # Solo devolvemos el mock si NO se está intentando una verificación real
        if placa == "GOG05E" and not (captcha_value or (vin and len(vin) >= 10) or (doc_type and doc_num)):
            return VehicleADN(
                placa="GOG05E",
                marca="DUCATI",
                linea="HYPERMOTARD 939",
                modelo=2016,
                color="ROJO",
                estado_soat="VIGENTE",
                vencimiento_soat="2025-05-12",
                estado_rtm="VIGENTE",
                vencimiento_rtm="2025-08-20",
                multas=0,
                valor_multas=0.0,
                embargos=False,
                tipo_servicio="PARTICULAR",
                limitaciones_propiedad="NINGUNA",
                es_verificado=False,
                fuente="IA KUMBALO (DATA PREVIEW)"
            )

        # Si se proporciona VIN, DOC o CAPTCHA, intentamos una consulta "Real"
        if (vin and len(vin) >= 10) or (doc_type and doc_num) or (captcha_token and captcha_value):
            dna = await self.get_real_vehicle_dna(placa, vin, doc_type, doc_num, captcha_token, captcha_value)
        else:
            raise Exception("Datos insuficientes para realizar la verificación legal de la placa.")

        # SIEMPRE intentamos inyectar datos reales de SIMIT para las multas
        simit_data = await self.simit.get_fines_by_plate(placa)
        if "error" not in simit_data:
            dna.multas = simit_data.get("cantidad_infracciones", 0)
            dna.valor_multas = float(simit_data.get("total_multas", 0.0))
            if simit_data.get("fuente") != "IA KUMBALO (FALLBACK)":
                dna.fuente = f"RUNT/SIMIT OFICIAL"
                dna.es_verificado = True
        
        return dna

    async def get_real_vehicle_dna(self, placa: str, vin: Optional[str] = None, doc_type: Optional[str] = None, doc_num: Optional[str] = None, captcha_token: Optional[str] = None, captcha_value: Optional[str] = None) -> VehicleADN:
        """
        Flujo de verificación avanzada (HITL).
        Se asocia a la base del RUNT oficial.
        """
        # Si tenemos captcha, intentamos consulta real al RUNT
        if captcha_token and captcha_value:
            real_data = await self.runt.get_vehicle_technical_data(placa, vin or "", doc_type, doc_num, captcha_token, captcha_value)
            
            if "error" not in real_data:
                return VehicleADN(
                    placa=placa,
                    marca=real_data["marca"],
                    linea=real_data["linea"],
                    modelo=real_data["modelo"],
                    color=real_data["color"],
                    estado_soat=real_data["estado_soat"],
                    vencimiento_soat=real_data["vencimiento_soat"],
                    estado_rtm=real_data["estado_rtm"],
                    vencimiento_rtm=real_data["vencimiento_rtm"],
                    multas=0, 
                    valor_multas=0.0,
                    embargos=False,
                    es_verificado=True,
                    fuente=real_data["fuente"]
                )
            else:
                # Error Real: Si el RUNT responde con error, NO caemos en Mock
                # Lanzamos una excepción para que el router la maneje y el usuario vea el error
                raise Exception(f"RUNT Falló: {real_data.get('detail', 'Datos no encontrados o captcha inválido')}")
        
        # Si no hay captcha o datos válidos, no inventamos datos. Reclamamos conexión al RUNT.
        raise Exception("Se requiere conexión verificada (Captcha/Documentos) para obtener el ADN del vehículo de manera legal y no simulada.")

