import httpx
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("kumbalo.simit")

class SimitAgent:
    """
    Agente especializado en la extracción de datos reales de SIMIT.
    Utiliza los microservicios oficiales de la Federación Colombiana de Municipios.
    """
    
    BASE_URL = "https://consultasimit.fcm.org.co/simit/microservices/estado-cuenta-simit/estadocuenta"
    
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://www.fcm.org.co",
            "Referer": "https://www.fcm.org.co/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }

    async def get_fines_by_plate(self, plate: str) -> Dict[str, Any]:
        """
        Consulta las multas reales de una placa específica.
        """
        plate = plate.upper().strip().replace("-", "")
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                payload = {
                    "filtro": plate,
                    "reCaptchaDTO": {
                        "hash": "", 
                        "valor": ""
                    }
                }
                
                logger.info(f"SIMIT: Consultando multas para placa {plate}")
                response = await client.post(f"{self.BASE_URL}/consulta", json=payload, headers=self.headers)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_results(data)
                    
                elif response.status_code == 403:
                    logger.warning(f"SIMIT Bloqueado por Captcha u Origen para placa {plate}.")
                    raise Exception("El servidor de multas SIMIT ha bloqueado la consulta temporalmente. Intente más tarde.")
                else:
                    logger.error(f"SIMIT Error {response.status_code}: {response.text}")
                    raise Exception(f"Error de comunicación con SIMIT: {response.status_code}")
                    
        except Exception as e:
            logger.error(f"Error crítico en SIMIT Agent: {str(e)}")
            raise

    def _parse_results(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parsea el JSON complejo de SIMIT a un formato plano para Kumbalo.
        """
        # Estructura típica de respuesta SIMIT (Resumen)
        return {
            "total_multas": data.get("totalGeneral", 0),
            "cantidad_infracciones": len(data.get("multas", [])),
            "estado": "VERIFICADO_REAL",
            "fuente": "SIMIT OFICIAL"
        }
