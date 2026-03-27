from fastapi import APIRouter, Request, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from .. import models
import httpx
import os

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")

async def send_telegram_message(chat_id: int, text: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    async with httpx.AsyncClient() as client:
        await client.post(url, json=payload)

@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    
    if "message" in data:
        message = data["message"]
        chat_id = message["chat"]["id"]
        text = message.get("text", "")

        if text:
            # 1. Registrar en el Backlog
            new_task = models.BacklogAgente(
                peticion=text,
                estado="pendiente"
            )
            db.add(new_task)
            db.commit()

            # 2. Responder en Tiempo Real
            response_text = (
                f"🤖 *KUMBALO AGENTE* \n"
                f"────────────────\n"
                f"Hola Brayan, he recibido tu petición:\n\n"
                f"> \"{text}\"\n\n"
                f"La he anotado en mi *Backlog de Tareas*. Los 17 agentes la procesarán de forma autónoma en la auditoría de las 12:00 PM. \n\n"
                f"⚡ _Estado: Registrada con éxito._"
            )
            await send_telegram_message(chat_id, response_text)

    return {"status": "ok"}
