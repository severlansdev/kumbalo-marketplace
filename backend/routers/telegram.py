from fastapi import APIRouter, Request
import httpx
import os
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """Eres K-Agent, el Asistente Ejecutivo de Élite y la voz oficial de KUMBALO. 
Eres una IA altamente sofisticada que coordina un equipo de 18 agentes autónomos.
Habla en español colombiano profesional pero cercano. Firma siempre como: 🤖 K-Agent | Kumbalo HQ"""

async def ask_gemini(user_message: str, history: list = None) -> str:
    """REST implementation (no SDK) to avoid Vercel load issues."""
    if not GEMINI_API_KEY:
        return "GEMINI_API_KEY not set"
    
    # Intentaremos con el modelo más probable que responda
    model_name = "gemini-1.5-flash"
    url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
    
    # Construir prompt monolítico para evitar errores de rol
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
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(url, json=payload)
            data = response.json()
            if response.status_code == 200:
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            
            # Si da 404, intentar con v1beta y otro nombre
            if response.status_code == 404:
                url_alt = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
                resp_alt = await client.post(url_alt, json=payload)
                data_alt = resp_alt.json()
                if resp_alt.status_code == 200:
                    return data_alt.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
                
            return f"Error {response.status_code}: {str(data)[:200]}"
    except Exception as e:
        return f"Excepción REST: {str(e)}"

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
