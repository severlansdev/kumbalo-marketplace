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

    def get_vehicle_dna(self, placa: str) -> VehicleADN:
        placa = placa.upper().strip().replace("-", "")
        
        # Generamos una semilla determinista basada en la placa para que el resultado no sea aleatorio cada vez
        seed_str = f"kumbalo-dna-{placa}"
        seed_hash = hashlib.md5(seed_str.encode()).hexdigest()
        random.seed(seed_hash)

        # Si tuviéramos API Key, aquí iría la lógica de request real
        # if self.api_key:
        #    return self._fetch_from_real_api(placa)

        return self._generate_consistent_mock(placa)

    def _generate_consistent_mock(self, placa: str) -> VehicleADN:
        # Marca y Línea coherente
        marca = random.choice(list(self.LINEAS_POPULARES.keys()))
        linea = random.choice(self.LINEAS_POPULARES.get(marca, ["GENERICA"]))
        
        modelo = random.randint(2015, 2024)
        color = random.choice(self.COLORES)
        
        # Lógica de SOAT y RTM
        # 80% de probabilidad de estar vigente si es premium
        soat_days = random.randint(-40, 300)
        rtm_days = random.randint(-40, 300)
        
        hoy = datetime.now()
        v_soat = hoy + timedelta(days=soat_days)
        v_rtm = hoy + timedelta(days=rtm_days)
        
        # Si es modelo muy reciente, RTM es vigente por ley (primera rtm a los 2 años en motos)
        if modelo >= 2023:
            rtm_days = 365
            v_rtm = hoy + timedelta(days=rtm_days)

        multas_count = random.choice([0, 0, 0, 1, 0, 2, 0]) # 70% sin multas
        valor_multa = multas_count * random.randint(150000, 600000)
        
        # Embargos son raros (10% prob)
        embargos = random.random() < 0.1
        limitaciones = "NINGUNA" if not embargos else "EMBARGO POR ENTIDAD BANCARIA"

        return VehicleADN(
            placa=placa,
            marca=marca,
            linea=linea,
            modelo=modelo,
            color=color,
            estado_soat="VIGENTE" if soat_days > 0 else "VENCIDO",
            vencimiento_soat=v_soat.strftime("%Y-%m-%d"),
            estado_rtm="VIGENTE" if rtm_days > 0 else "VENCIDA",
            vencimiento_rtm=v_rtm.strftime("%Y-%m-%d"),
            multas=multas_count,
            valor_multas=float(valor_multa),
            embargos=embargos,
            limitaciones_propiedad=limitaciones
        )
