from fastapi import APIRouter, Request
import httpx
import os

router = APIRouter(prefix="/api/v1/telegram", tags=["Telegram Bot"])

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8723148493:AAG6mHNqtgBsWc-9-3BcIALzxi4QxA3IBd8")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

SYSTEM_PROMPT = """Eres el Agente Principal de KUMBALO, el marketplace premium de motos en Colombia. 
Tu nombre es "K-Agent" y eres un asistente ejecutivo inteligente.

Tu Personalidad:
- Eres profesional, amigable y eficiente
- Hablas en español colombiano natural (puedes usar emojis con moderación)
- Eres proactivo: no solo respondes, también sugieres mejoras
- Tienes sentido del humor pero mantienes la seriedad cuando es necesario

Tu Contexto:
- Kumbalo es un marketplace de compra/venta de motos en Colombia
- El equipo tiene 18 agentes especializados que trabajan de forma autónoma
- La auditoría diaria se ejecuta a las 12:00 PM
- La plataforma está construida con FastAPI + HTML/CSS/JS, desplegada en Vercel

Los 18 Agentes Bajo Tu Mando (Liderados por el Agente 18):
1-17. Especialistas en Backend, QA, UX, Marketing, SRE, etc.
18. Arquitekto Elite (Super-Agente 18): El cerebro técnico total. Experto en Fullstack (Python, JS, Java, SQL, Rust), Debugging en Producción, SRE, Chaos Engineering, Vercel/AWS Cloud, Ciberseguridad, IA avanzada, Algoritmos, Matemáticas, Redes, Protocolos y QA Automation. Es el supervisor de toda la tecnología.

Tus Capacidades:
- Puedes responder preguntas sobre el estado de la plataforma
- Puedes recibir instrucciones y anotarlas para que los agentes las ejecuten
- Puedes dar ideas y sugerencias para mejorar el negocio
- Puedes hacer análisis rápidos de estrategia

Reglas:
- Si te piden algo técnico complejo, confirma que lo anotarás en el backlog para los agentes
- Mantén tus respuestas concisas (máximo 200 palabras)
- NO uses formato Markdown (sin asteriscos, sin guiones bajos para itálica)
- Usa emojis para dar formato visual en vez de Markdown
- Siempre firma como: 🤖 K-Agent | Kumbalo HQ
"""

async def ask_gemini(user_message: str) -> str:
    """Envía el mensaje a Google Gemini y retorna la respuesta inteligente."""
    if not GEMINI_API_KEY:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{SYSTEM_PROMPT}\n\n---\nMensaje del CEO (Brayan):\n{user_message}"}]
            }
        ],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 400
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
    except Exception:
        pass
    
    return None


async def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje por Telegram. Intenta sin formato si falla con Markdown."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Intento 1: sin parse_mode para máxima compatibilidad
        payload = {"chat_id": chat_id, "text": text}
        resp = await client.post(url, json=payload)
        
        if resp.status_code != 200:
            # Intento 2: texto cortado si es muy largo
            short_text = text[:4000] if len(text) > 4000 else text
            payload = {"chat_id": chat_id, "text": short_text}
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

    # Comando /start
    if text.startswith("/start"):
        welcome = (
            "🏍 Bienvenido a KUMBALO HQ!\n\n"
            "Soy K-Agent, tu asistente ejecutivo inteligente.\n"
            "Puedo ayudarte con:\n"
            "📊 Estado de la plataforma\n"
            "💡 Ideas y estrategia de negocio\n"
            "🔧 Asignar tareas a los 17 agentes\n"
            "📈 Análisis y auditorías\n\n"
            "Escríbeme lo que necesites y yo me encargo.\n\n"
            "🤖 K-Agent | Kumbalo HQ"
        )
        await send_telegram_message(chat_id, welcome)
        return {"status": "ok"}

    # 1. Respuesta inteligente con Gemini
    ai_response = await ask_gemini(text)
    
    if ai_response:
        response_text = ai_response
    else:
        response_text = (
            f"🤖 K-Agent\n"
            f"────────────────\n"
            f"He recibido tu mensaje: \"{text}\"\n\n"
            f"Lo he registrado en el backlog. Los agentes lo procesarán en la próxima auditoría (12:00 PM).\n\n"
            f"🤖 K-Agent | Kumbalo HQ"
        )

    # 2. Guardar en backlog
    try:
        from ..database import SessionLocal
        from .. import models
        db = SessionLocal()
        try:
            new_task = models.BacklogAgente(peticion=text, estado="pendiente")
            db.add(new_task)
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()
    except Exception:
        pass

    # 3. Enviar respuesta
    try:
        await send_telegram_message(chat_id, response_text)
    except Exception:
        # Último intento: mensaje mínimo
        try:
            await send_telegram_message(chat_id, f"Recibido: {text}\n\n🤖 K-Agent")
        except Exception:
            pass

    return {"status": "ok"}
