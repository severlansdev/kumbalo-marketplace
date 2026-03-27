import time
import sys
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="KUMBALO API")

# --- Guarded heavy imports (may fail on serverless) ---
try:
    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)
except Exception:
    pass  # Prometheus not available on Vercel

try:
    from slowapi import _rate_limit_exceeded_handler
    from slowapi.errors import RateLimitExceeded
    from .limiter import limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
except Exception:
    pass  # slowapi not critical for serverless

# --- Database (lazy startup) ---
from .database import engine
from . import models

@app.on_event("startup")
def on_startup():
    from .database import SessionLocal
    from . import models
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    except ImportError:
        print("⚠️ [WARN] Passlib/Bcrypt not found. Admin setup skipped.")
        return

    try:
        models.Base.metadata.create_all(bind=engine)
        db = SessionLocal()
        email = "brayanpd23@gmail.com"
        user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
        
        if not user:
            new_admin = models.Usuario(
                nombre="Director Kumbalo",
                email=email,
                hashed_password=pwd_context.hash("admin123"),
                rol="admin",
                tipo_cuenta="concesionario",
                is_pro=True
            )
            db.add(new_admin)
            db.commit()
            print(f"✅ [SETUP] Created Admin: {email}")
        elif user.rol != "admin":
            user.rol = "admin"
            db.commit()
            print(f"🛡️ [SETUP] Promoted: {email}")
        db.close()
    except Exception as e:
        print(f"❌ [STARTUP_ERROR] {e}")

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging middleware ---
try:
    from .logging_config import logger, log_request

    @app.middleware("http")
    async def logging_middleware(request: Request, call_next):
        start = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start) * 1000
        log_request(request.method, str(request.url.path), response.status_code, duration_ms)
        return response
except Exception:
    pass

# --- Root endpoints ---
@app.get("/")
def read_root():
    return {"message": "🚀 Bienvenido al API del Marketplace de Motos (Fullstack Edition)"}

@app.get("/api/health")
@app.get("/api/v1/health")
@app.get("/health")
def health_check():
    import os
    return {
        "status": "healthy",
        "service": "kumbalo-api",
        "version": "1.0.0",
        "env_checks": {
            "gemini_api_key": "set" if os.getenv("GEMINI_API_KEY") else "missing",
            "telegram_bot_token": "set" if os.getenv("TELEGRAM_BOT_TOKEN") else "using_default",
            "telegram_router_active": "telegram" in globals() or "telegram" in sys.modules,
            "all_keys": list(os.environ.keys())
        }
    }

# --- Routers (guarded) ---
try:
    from .routers import auth
    app.include_router(auth.router)
except Exception as e:
    print(f"[WARN] Could not load auth router: {e}")

try:
    from .routers import motos
    app.include_router(motos.router)
except Exception as e:
    print(f"[WARN] Could not load motos router: {e}")

try:
    from .routers import mensajes
    app.include_router(mensajes.router)
except Exception as e:
    print(f"[WARN] Could not load mensajes router: {e}")

try:
    from .routers import payments
    app.include_router(payments.router)
except Exception as e:
    print(f"[WARN] Could not load payments router: {e}")

try:
    from .routers import chat
    app.include_router(chat.router)
except Exception as e:
    print(f"[WARN] Could not load chat router: {e}")

try:
    from .routers import telegram
    app.include_router(telegram.router)
except Exception as e:
    print(f"[WARN] Could not load telegram router: {e}")

try:
    from .routers import agents
    app.include_router(agents.router, prefix="/api/v1")
except Exception as e:
    print(f"[WARN] Could not load agents router: {e}")

try:
    from .routers import runt
    app.include_router(runt.router, prefix="/api/v1/runt", tags=["RUNT Lead Magnet"])
except Exception as e:
    print(f"[WARN] Could not load runt router: {e}")
