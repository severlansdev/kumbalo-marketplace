from fastapi import APIRouter, Request
import httpx
import os
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

# Credenciales (Fijas temporalmente para asegurar el éxito, luego el CEO las mueve a Vercel)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDAuaA2CW5J2CcGFiU74WbZNly136fE2TA")

SYSTEM_PROMPT = """Eres K-Agent, la Mano Derecha y el Asistente Ejecutivo PERSONAL de Brayan (CEO de KUMBALO).
Tu misión es EXCLUSIVA para el nivel C-Suite. NO eres un bot para el público.
Coordinas a los 18 agentes especialistas para que Brayan tenga el control total del negocio.
Reporta estados, analiza estrategias y mantén la confidencialidad absoluta.
Firma siempre como: 🕴️ K-Agent | Mano Derecha del CEO"""

async def ask_gemini(user_message: str, history: list = None) -> str:
    """REST implementation targeting Gemini 2.5/2.0 generations."""
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY no configurada."
    
    # Modelos confirmados por descubrimiento directo en el servidor
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite",
        "gemini-2.0-flash",
        "gemini-2.0-flash-001"
    ]
    
    full_prompt = f"{SYSTEM_PROMPT}\n\n"
    if history:
        for entry in history:
            label = "CEO" if entry["role"] == "user" else "K-Agent"
            full_prompt += f"{label}: {entry['content']}\n"
    full_prompt += f"\nCEO Brayan: {user_message}"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 1000}
    }
    
    last_error = ""
    async with httpx.AsyncClient(timeout=20.0) as client:
        for model in models_to_try:
            # Usamos v1beta para máxima compatibilidad con 2.5+
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            try:
                response = await client.post(url, json=payload)
                data = response.json()
                if response.status_code == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                
                last_error = f"{model} ({response.status_code}) - {str(data)[:100]}"
            except Exception as e:
                last_error = f"{model} exc: {str(e)}"
    
    return f"Sinergia de Nueva Generación Fallida. Último error: {last_error}. CEO, por favor verifica el AI Studio."

@router.post("/webhook")
async def telegram_webhook(request: Request):
    try:
        data = await request.json()
    except Exception: return {"status": "ok"}
    if "message" not in data: return {"status": "ok"}
    message = data["message"]
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")
    if not chat_id or not text: return {"status": "ok"}

    history_entries = []
    try:
        db = SessionLocal()
        recent = db.query(models.TelegramHistory).filter(models.TelegramHistory.chat_id == str(chat_id)).order_by(models.TelegramHistory.id.desc()).limit(10).all()
        history_entries = [{"role": h.role, "content": h.content} for h in reversed(recent)]
        db.close()
    except Exception: pass

    response_text = await ask_gemini(text, history_entries)

    try:
        db = SessionLocal()
        db.add(models.TelegramHistory(chat_id=str(chat_id), role="user", content=text))
        db.add(models.TelegramHistory(chat_id=str(chat_id), role="model", content=response_text))
        db.commit()
        db.close()
    except Exception: pass

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient() as client:
        await client.post(url, json={"chat_id": chat_id, "text": response_text})
    
    return {"status": "ok"}
