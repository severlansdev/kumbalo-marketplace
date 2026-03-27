import os
import requests
from dotenv import load_dotenv

load_dotenv()

class NotificationManager:
    """
    Clase centralizada para que los 17 Agentes de Kumbalo 
    se comuniquen con el Director (Brayan) vía WhatsApp o Discord.
    """
    
    def __init__(self):
        self.whatsapp_number = os.getenv("WHATSAPP_NUMBER", "+573016702548")
        self.whatsapp_api_url = os.getenv("WHATSAPP_API_URL") # Ejemplo: Twilio o Wati
        self.whatsapp_token = os.getenv("WHATSAPP_API_TOKEN")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    def send_whatsapp(self, message: str):
        """Envía una notificación de WhatsApp al Director."""
        if not self.whatsapp_api_url or not self.whatsapp_token:
            print(f"[LOG] Notificación WhatsApp (Simulada): {message}")
            return False
            
        payload = {
            "to": self.whatsapp_number,
            "message": message
        }
        headers = {
            "Authorization": f"Bearer {self.whatsapp_token}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(self.whatsapp_api_url, json=payload, headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Error enviando WhatsApp: {e}")
            return False

    def send_approval_request(self, agent_name: str, proposal_title: str, link: str):
        """Solicita aprobación específica para un cambio técnico."""
        msg = (
            f"🚀 *KUMBALO AI - SOLICITUD DE APROBACIÓN*\n\n"
            f"🤖 *Agente*: {agent_name}\n"
            f"📝 *Propuesta*: {proposal_title}\n"
            f"🔗 *Revisar aquí*: {link}\n\n"
            f"Responde 'SÍ' para autorizar el despliegue automático."
        )
        return self.send_whatsapp(msg)

# Instancia global para ser usada por otros scripts de agentes
notifier = NotificationManager()
