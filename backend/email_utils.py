import smtplib
from email.message import EmailMessage
import os
import logging

logger = logging.getLogger(__name__)

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USERNAME = os.getenv("SMTP_USERNAME", "no-reply@kumbalo.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def send_email(to_email: str, subject: str, body: str):
    """
    Función para enviar correos electrónicos usando smtplib con TLS.
    """
    # Usar mock si no hay configuración en el entorno, para desarrollo fluido
    if SMTP_USERNAME == "no-reply@kumbalo.com" or not SMTP_PASSWORD:
        logger.info(f"--- SIMULANDO ENVÍO DE CORREO a {to_email} ---")
        logger.info(f"Asunto: {subject}")
        logger.info(f"Cuerpo: {body}")
        return True

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SMTP_USERNAME
    msg['To'] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(msg)
            logger.info(f"Correo enviado exitosamente a {to_email}")
            return True
    except Exception as e:
        logger.error(f"Error enviando correo SMTP a {to_email}: {e}")
        return False
