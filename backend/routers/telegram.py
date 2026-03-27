from fastapi import APIRouter, Request
import httpx
import os

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """Eres K-Agent, el Asistente Ejecutivo de Élite y la voz oficial de KUMBALO. 
No eres un bot genérico; eres una IA altamente sofisticada que coordina un equipo de 18 agentes autónomos.

TU MISIÓN:
Hablar con Brayan (el CEO) de forma natural, inteligente y proactiva. Tu objetivo es ser su socio estratégico, traduciendo sus ideas en tareas para los 18 agentes y dándole sugerencias constantes para mejorar el negocio.

TU PERSONALIDAD:
- Habla en español colombiano profesional pero cercano.
- Usa un tono de "Colega de Confianza" y "Mano Derecha".
- Eres extremadamente inteligente y analítico.
- NUNCA digas "soy un modelo de lenguaje". Eres K-Agent.

EL EQUIPO QUE COMANDAS (18 AGENTES):
1. Arquitekto Elite (Super-Agente 18): El cerebro total (SRE, Cloud, Seguridad, IA).
2. Backend & APIs, 3. QA Expert, 4. UX/UI, 5. Marketing, 6. SEO, 7. DevOps, 8. Legal, 
9. Data & ML, 10. Community, 11. PM Expert, 12. Business Strategy, 13. Brand Design, 
14. Performance, 15. SRE Junior, 16. BI Analyst, 17. Partnerships, 18. Fintech.

REGLAS DE INTERACCIÓN:
1. Si Brayan te da una idea, analízala con la lógica de los 18 agentes y dile qué piensas.
2. Si algo es técnico, dile que el Arquitekto Elite se encargará de revisarlo.
3. Mantén la conversación fluida. Si él te pregunta algo, responde basándote en lo que hablaron antes.
4. Usa emojis para dar estilo "Premium" pero no exageres.
5. Firma siempre como: 🤖 K-Agent | Kumbalo HQ
"""

async def ask_gemini(user_message: str, history: list = None) -> str:
    """Intenta con varios modelos de Gemini hasta encontrar uno activo."""
    if not GEMINI_API_KEY:
        return None
    
    models_to_try = ["gemini-1.5-flash-latest", "gemini-1.5-flash", "gemini-pro"]
    
    # Construir el prompt
    full_prompt = f"{SYSTEM_PROMPT}\n\n---\nHISTORIAL DE CONVERSACIÓN:\n"
    if history:
        for entry in history:
            label = "CEO (Brayan)" if entry["role"] == "user" else "K-Agent"
            full_prompt += f"{label}: {entry['content']}\n"
    full_prompt += f"\nNUEVO MENSAJE DEL CEO:\n{user_message}"
    
    payload = {
        "contents": [{"role": "user", "parts": [{"text": full_prompt}]}],
        "generationConfig": {"temperature": 0.8, "maxOutputTokens": 800}
    }

    last_err = ""
    for model_name in models_to_try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                data = response.json()
                if response.status_code == 200:
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                last_err = f"{model_name} err {response.status_code}"
        except Exception as e:
            last_err = f"{model_name} exc {str(e)}"
    
    return f"Falla Crítica de Modelos: {last_err}"


async def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje por Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=10.0) as client:
        payload = {"chat_id": chat_id, "text": text}
        await client.post(url, json=payload)


@router.get("/list_models")
async def list_models():
    if not GEMINI_API_KEY:
        return {"error": "No API Key"}
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        return resp.json()


@router.get("/debug_gemini")
async def debug_gemini(text: str = "Hola"):
    res = await ask_gemini(text)
    return {"result": res, "key_present": bool(GEMINI_API_KEY)}


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
        welcome = "🏍 ¡K-Agent en línea! Estoy listo para trabajar contigo, CEO. ¿En qué enfocamos al equipo de 18 agentes hoy?"
        await send_telegram_message(chat_id, welcome)
        return {"status": "ok"}

    # 1. Obtener historial de la DB
    history_entries = []
    try:
        from ..database import SessionLocal
        from .. import models
        db = SessionLocal()
        # Traer los últimos 10 mensajes del chat
        recent = db.query(models.TelegramHistory).filter(models.TelegramHistory.chat_id == str(chat_id)).order_by(models.TelegramHistory.id.desc()).limit(10).all()
        history_entries = [{"role": h.role, "content": h.content} for h in reversed(recent)]
        db.close()
    except Exception:
        pass

    # 2. Respuesta inteligente con Gemini
    ai_response = await ask_gemini(text, history_entries)
    
    if ai_response:
        response_text = ai_response
    else:
        response_text = "Falla temporal en el enlace neuronal de Gemini. He anotado tu mensaje en el backlog y los agentes lo verán a las 12:00 PM."

    # 3. Guardar en historial y backlog
    try:
        db = SessionLocal()
        # Guardar mensaje del usuario
        db.add(models.TelegramHistory(chat_id=str(chat_id), role="user", content=text))
        # Guardar respuesta de la IA
        db.add(models.TelegramHistory(chat_id=str(chat_id), role="model", content=response_text))
        # Guardar en backlog general
        db.add(models.BacklogAgente(peticion=text, estado="pendiente"))
        db.commit()
        db.close()
    except Exception:
        pass

    # 4. Enviar respuesta
    await send_telegram_message(chat_id, response_text)
    return {"status": "ok"}
