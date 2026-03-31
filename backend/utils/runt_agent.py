import httpx
import logging
import base64
from typing import Dict, Any, Optional

logger = logging.getLogger("kumbalo.runt")

class RuntAgent:
    """
    Agente especializado en la extracción de datos técnicos del RUNT.
    Maneja la lógica de consulta por placa y VIN.
    """
    
    BASE_URL = "https://runtproapi.runt.gov.co/CYRConsultaVehiculoMS/"
    
    # Diccionario para persistir cookies de sesión vinculadas al captcha ID
    session_cookies = {}

    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "x-funcionalidad": "SHELL",
            "Origin": "https://portalpublico.runt.gov.co",
            "Referer": "https://portalpublico.runt.gov.co/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9",
            "Accept-Encoding": "gzip, deflate, br"
        }

    async def get_captcha(self) -> Dict[str, Any]:
        """
        Obtiene un nuevo captcha del RUNT. 
        """
        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(f"{self.BASE_URL}captcha/libre-captcha/generar", headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    captcha_id = data.get("id")
                    raw_img = data.get("imagen") or data.get("base64")
                    
                    if not raw_img:
                        return {"error": "EMPTY_IMAGE"}

                    self.session_cookies[captcha_id] = response.cookies
                    if not str(raw_img).startswith("data:image"):
                        raw_img = f"data:image/png;base64,{raw_img}"
                        
                    return {"id": captcha_id, "imagen": raw_img}
                return {"error": "CAPTCHA_FAILED", "status": response.status_code}
        except Exception as e:
            return {"error": str(e)}

    async def get_vehicle_technical_data(self, plate: str, vin: str = None, doc_type: str = "C", doc_num: str = None, captcha_token: str = None, captcha_value: str = None) -> Dict[str, Any]:
        tipo_consulta = "2" if vin else "1"
        
        payload = {
            "procedencia": "NACIONAL",
            "tipoConsulta": tipo_consulta,
            "placa": plate.upper().strip(),
            "tipoDocumento": doc_type or "C",
            "documento": doc_num.strip() if doc_num else "",
            "idLibreCaptcha": captcha_token or "",
            "captcha": captcha_value.strip() if captcha_value else "", # NO .upper()
            "verBannerSoat": True,
            "configuracion": {
                "tiempoInactividad": "900",
                "tiempoCuentaRegresiva": "10"
            }
        }
        
        if vin:
            payload["vin"] = vin.upper().strip()
        
        cookies = self.session_cookies.get(captcha_token)
        
        try:
            async with httpx.AsyncClient(timeout=30.0, cookies=cookies) as client:
                response = await client.post(f"{self.BASE_URL}auth", json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    if captcha_token in self.session_cookies:
                        del self.session_cookies[captcha_token]
                    
                    data = response.json()
                    # RUNT suele devolver 'infoVehiculo' o directamente el objeto
                    if data.get("infoVehiculo") or data.get("vehiculo"):
                        return self._parse_technical_data(data)
                    
                    detail = data.get("mensaje") or "Los datos no coinciden en el RUNT oficial."
                    return {"error": "DATA_MISMATCH", "detail": detail}
                
                # Hacker Guardian: Loggear error para diagnóstico
                logger.error(f"RUNT 400 Payload: {payload}")
                logger.error(f"RUNT Response: {response.text}")
                
                return {"error": "RUNT_ERR", "detail": f"Error del servidor RUNT ({response.status_code})"}
        except Exception as e:
            return {"error": "CONN_FAILED", "detail": str(e)}

    def _parse_technical_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        vehiculo = data.get("infoVehiculo") or data.get("vehiculo") or data.get("resumentTecnico") or {}
        soat = data.get("soat") or {}
        rtm = data.get("revisionTecnomecanica") or {}
        
        return {
            "marca": vehiculo.get("marca", "DESCONOCIDA"),
            "linea": vehiculo.get("linea", "DESCONOCIDA"),
            "modelo": vehiculo.get("modelo", 0),
            "color": vehiculo.get("color", "DESCONOCIDO"),
            "estado_soat": "VIGENTE" if soat.get("estado") == "VIGENTE" else "VENCIDO",
            "vencimiento_soat": soat.get("fechaVencimiento", "N/A"),
            "estado_rtm": "VIGENTE" if rtm.get("estado") == "VIGENTE" else "VENCIDA",
            "vencimiento_rtm": rtm.get("fechaVencimiento", "N/A"),
            "fuente": "RUNT OFICIAL (VERIFICACIÓN TOTAL)"
        }

    def get_mock_verified_data(self, plate: str, vin: str) -> Dict[str, Any]:
        return {
            "marca": "DUCATI" if vin.startswith("ZDM") else "YAMAHA",
            "modelo": 2010 + int(vin[9]) if len(vin) > 9 and vin[9].isdigit() else 2020,
            "es_verificado": True,
            "fuente": "RUNT (VERIFICADO POR VIN)"
        }
