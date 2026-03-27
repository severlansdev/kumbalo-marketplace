from fastapi import APIRouter, Request
import httpx
import os
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyDAuaA2CW5J2CcGFiU74WbZNly136fE2TA")

SYSTEM_PROMPT = """Eres K-Agent, el Asistente Ejecutivo de Élite y la voz oficial de KUMBALO. 
Eres una IA altamente sofisticada que coordina un equipo de 18 agentes autónomos.
Habla en español colombiano profesional pero cercano. Firma siempre como: 🤖 K-Agent | Kumbalo HQ"""

async def ask_gemini(user_message: str, history: list = None) -> str:
    """Intenta con varios modelos de Gemini para encontrar uno con cuota y acceso."""
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY no configurada."
    
    # Priorizamos 2.0 porque es el que la cuenta reconoce (aunque diera 429)
    # y probamos versiones experimentales que suelen tener cuota propia.
    models_to_try = [
        "gemini-2.0-flash-exp",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]
    
    full_prompt = f"{SYSTEM_PROMPT}\n\n"
    if history:
        for entry in history:
            label = "CEO" if entry["role"] == "user" else "K-Agent"
            full_prompt += f"{label}: {entry['content']}\n"
    full_prompt += f"\nCEO Brayan: {user_message}"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 800}
    }
    
    last_error = ""
    async with httpx.AsyncClient(timeout=15.0) as client:
        for model in models_to_try:
            # Intentar primero con v1beta (más flexible para modelos nuevos)
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
                
                # Si es 429 (Agotado), seguimos al siguiente modelo
                # Si es 404 (No encontrado), seguimos al siguiente modelo
                last_error = f"{model} ({response.status_code})"
                
                # Caso especial: si es 404, intentar con v1 (estable) antes de saltar
                if response.status_code == 404:
                    url_v1 = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={GEMINI_API_KEY}"
                    resp_v1 = await client.post(url_v1, json=payload)
                    if resp_v1.status_code == 200:
                        data_v1 = resp_v1.json()
                        return data_v1.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")

            except Exception as e:
                last_error = f"{model} exc: {str(e)}"
    
    return f"Sinergia Fallida. Último intento: {last_error}. CEO, por favor verifica si la API Key en Vercel es correcta o si tiene habilitado Gemini 1.5/2.0 en AI Studio."

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
        recent = db.query(models.TelegramHistory).filter(models.TelegramHistory.chat_id == str(chat_id)).order_by(models.TelegramHistory.id.desc()).limit(5).all()
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
