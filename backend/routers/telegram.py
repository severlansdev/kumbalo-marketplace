from fastapi import APIRouter, Request
import httpx
import os
import google.generativeai as genai
from ..database import SessionLocal
from .. import models

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

# Configurar SDK
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY, transport='rest')

SYSTEM_PROMPT = """Eres K-Agent, el Asistente Ejecutivo de Élite y la voz oficial de KUMBALO. 
Eres una IA altamente sofisticada que coordina un equipo de 18 agentes autónomos.
Habla en español colombiano profesional pero cercano. Eres el socio estratégico de Brayan (el CEO).
Mantén la conversación fluida y recuerda el historial. Firma siempre como: 🤖 K-Agent | Kumbalo HQ"""

async def ask_gemini_sdk(user_message: str, history_entries: list = None) -> str:
    """Usa el SDK oficial para máxima compatibilidad."""
    if not GEMINI_API_KEY:
        return "Error: GEMINI_API_KEY no configurada."
    
    try:
        # Intentar con 1.5 Flash (el más resiliente)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Convertir historial al formato del SDK
        chat_history = []
        if history_entries:
            for h in history_entries:
                role = "user" if h["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [h["content"]]})
        
        chat = model.start_chat(history=chat_history)
        # Añadir el system prompt como pre-mensaje si no hay historial
        full_message = f"{SYSTEM_PROMPT}\n\nCEO Brayan dice: {user_message}"
        
        response = chat.send_message(full_message)
        return response.text
    except Exception as e:
        # Si falla 1.5, intentar fallback a 2.0 experimental
        try:
            model_exp = genai.GenerativeModel('gemini-2.0-flash-exp')
            response = model_exp.generate_content(f"{SYSTEM_PROMPT}\n\n{user_message}")
            return response.text
        except Exception as e2:
            return f"Error SDK Agotado: {str(e)} | Feedback 2.0: {str(e2)}"


async def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje por Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {"chat_id": chat_id, "text": text}
        await client.post(url, json=payload)


@router.get("/list_models")
async def list_models():
    try:
        models_list = []
        for m in genai.list_models():
            models_list.append(m.name)
        return {"available_models": models_list}
    except Exception as e:
        return {"error": str(e)}


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

    if text.startswith("/start"):
        welcome = "🏍 ¡K-Agent en línea! Mi núcleo ha sido actualizado a la tecnología SDK oficial. ¿Qué tenemos hoy, CEO?"
        await send_telegram_message(chat_id, welcome)
        return {"status": "ok"}

    # 1. Obtener historial
    history_entries = []
    try:
        db = SessionLocal()
        recent = db.query(models.TelegramHistory).filter(models.TelegramHistory.chat_id == str(chat_id)).order_by(models.TelegramHistory.id.desc()).limit(8).all()
        history_entries = [{"role": h.role, "content": h.content} for h in reversed(recent)]
        db.close()
    except Exception:
        pass

    # 2. Respuesta con SDK
    response_text = await ask_gemini_sdk(text, history_entries)

    # 3. Guardar historial
    try:
        db = SessionLocal()
        db.add(models.TelegramHistory(chat_id=str(chat_id), role="user", content=text))
        db.add(models.TelegramHistory(chat_id=str(chat_id), role="model", content=response_text))
        db.add(models.BacklogAgente(peticion=text, estado="pendiente"))
        db.commit()
        db.close()
    except Exception:
        pass

    # 4. Enviar
    await send_telegram_message(chat_id, response_text)
    return {"status": "ok"}
