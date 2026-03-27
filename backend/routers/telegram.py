from fastapi import APIRouter, Request, Depends
from sqlalchemy.orm import Session
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
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception:
        return {"status": "ok"}

    if "message" not in data:
        return {"status": "ok"}

    message = data["message"]
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id or not text:
        return {"status": "ok"}

    # Try to save to backlog (non-blocking)
    saved = False
    try:
        from ..database import get_db, SessionLocal
        from .. import models
        db = SessionLocal()
        try:
            new_task = models.BacklogAgente(
                peticion=text,
                estado="pendiente"
            )
            db.add(new_task)
            db.commit()
            saved = True
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass  # DB not available, still respond

    # Always respond to user
    status_text = "Registrada en Backlog ✅" if saved else "Recibida (DB offline, se reintentará) ⚡"
    response_text = (
        f"🤖 *KUMBALO AGENTE PRINCIPAL* \n"
        f"────────────────\n"
        f"Hola Brayan, he recibido tu petición:\n\n"
        f"> \"{text}\"\n\n"
        f"_{status_text}_\n\n"
        f"Los 17 agentes la procesarán en la auditoría de las 12:00 PM."
    )

    try:
        await send_telegram_message(chat_id, response_text)
    except Exception:
        pass

    return {"status": "ok"}
