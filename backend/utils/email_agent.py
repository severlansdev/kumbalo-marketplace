import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_transactional_email(to_email: str, subject: str, html_content: str) -> bool:
    """
    Envía un correo electrónico transaccional usando SMTP.
    Requiere las variables de entorno:
    - SMTP_HOST
    - SMTP_PORT
    - SMTP_USER
    - SMTP_PASS
    """
    smtp_host = os.environ.get("SMTP_HOST")
    smtp_port = os.environ.get("SMTP_PORT")
    smtp_user = os.environ.get("SMTP_USER")
    smtp_pass = os.environ.get("SMTP_PASS")

    # Si no están configuradas en dev, imprimirlas a la consola como MOCK
    if not all([smtp_host, smtp_port, smtp_user, smtp_pass]):
        print(f"📧 [EMAIL MOCK] Para: {to_email} | Asunto: {subject}")
        print(html_content)
        return True

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Kumbalo Automotriz <{smtp_user}>"
    msg["To"] = to_email

    part = MIMEText(html_content, "html")
    msg.attach(part)

    try:
        server = smtplib.SMTP(smtp_host, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(msg["From"], to_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"❌ Error enviando email a {to_email}: {e}")
        return False

# ----- PLATILLAS PREDISEÑADAS (LEADS Y FINTECH) -----

def notify_nueva_puja(vendedor_email: str, marca: str, monto: float):
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #FF2800;">¡Recibiste una nueva puja en tu subasta!</h2>
        <p>Un concesionario VIP acaba de elevar la apuesta por tu <b>{marca}</b> en el entorno C2B.</p>
        <h3 style="background:#f4f4f4; padding:10px; border-radius:5px;">Mejor Oferta Actual: ${monto:,.0f} COP</h3>
        <p>Entra a tu Garage Virtual para verificar la sala de subastas.</p>
        <p>Saludos,<br>El equipo de Kumbalo.</p>
    </div>
    """
    send_transactional_email(vendedor_email, f"🔥 ¡Nueva Puja Registrada! - {marca}", html)


def notify_estado_permuta(receptor_email: str, moto_ofrecida: str, moto_objetivo: str, estado: str):
    color = "#10b981" if estado == "aceptada" else "#ef4444"
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: {color};">Tu oferta de permuta ha sido {estado.upper()}</h2>
        <p>El usuario ha <b>{estado}</b> hacer Trade-In intercambiando su {moto_objetivo} por tu {moto_ofrecida}.</p>
    """
    if estado == "aceptada":
        html += "<p>🏦 <b>Siguiente paso:</b> Hemos iniciado la retención Dual-Escrow. Ingresa al Dashboard de Gestión de Trámites para subir tus documentos del RUNT.</p>"
        
    html += """
        <p>Saludos,<br>Gestión Escrow - Kumbalo.</p>
    </div>
    """
    send_transactional_email(receptor_email, f"Actualización de Oferta Trade-In - {estado.capitalize()}", html)


def notify_traspaso_pagado(comprador_email: str, tramite_id: int):
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333;">
        <h2 style="color: #FF2800;">Pago de Traspaso Exitoso (Double Escrow)</h2>
        <p>Tu dinero ha sido retenido de forma segura en las bóvedas virtuales de nuestro procesador aliado.</p>
        <p>El identificador de Trámite Legal #<b>{tramite_id}</b> fue activado.</p>
        <p>Sube las fotos de tu cédula y nosotros redactaremos automáticamente el mandato legal (FUN) en la plataforma B2B con los notarios designados.</p>
        <p>Gracias por confiar en el Fintech de Kumbalo.</p>
    </div>
    """
    send_transactional_email(comprador_email, f"⚖️ Pago Exitoso Traspaso Legal #{tramite_id}", html)
