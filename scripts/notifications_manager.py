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
        self.telegram_token = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "1597264470")
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    def send_telegram(self, message: str):
        """Envía una notificación de Telegram al Director (Brayan)."""
        if not self.telegram_token or not self.telegram_chat_id:
            print(f"[LOG] Notificación Telegram (Simulada): {message}")
            return False
            
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            "chat_id": self.telegram_chat_id,
            "text": message,
            "parse_mode": "Markdown"
        }
        
        try:
            response = requests.post(url, json=payload)
            return response.status_code == 200
        except Exception as e:
            print(f"[ERROR] Error enviando Telegram: {e}")
            return False

    def send_approval_request(self, agent_name: str, proposal_title: str, link: str):
        """Solicita aprobación específica para un cambio técnico."""
        msg = (
            f"🚀 *KUMBALO AI - SOLICITUD DE APROBACIÓN*\n\n"
            f"🤖 *Agente*: {agent_name}\n"
            f"📝 *Propuesta*: {proposal_title}\n"
            f"🔗 *Revisar aquí*: {link}\n\n"
            f"Responde a este mensaje para autorizar el cambio."
        )
        return self.send_telegram(msg)

# Instancia global para ser usada por otros scripts de agentes
notifier = NotificationManager()
