"""
KUMBALO API - Servidor Principal de la Plataforma de Marketplace de Motos.
Este módulo inicializa FastAPI, configura middleware (CORS, Sentry, Prometheus),
gestiona la sincronización automática de la base de datos y registra los routers.
"""
import time
import sys
import os
from typing import Optional, Tuple
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI(
    title="KUMBALO API",
    description="Motor autónomo para el marketplace de motos premium con integración de agentes IA y servicios de trámite.",
    version="1.1.0"
)

# --- Guarded heavy imports (may fail on serverless) ---
try:
    import sentry_sdk
    import os
    if os.environ.get("SENTRY_DSN"):
        sentry_sdk.init(
            dsn=os.environ.get("SENTRY_DSN"),
            traces_sample_rate=1.0,
            profiles_sample_rate=1.0,
        )
except Exception:
    pass

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

def sync_db_schema(engine, models, SessionLocal, pwd_context) -> Tuple[bool, Optional[str]]:
    """
    Sincroniza el esquema de la base de datos y aplica parches manuales necesarios.
    
    Este método asegura que las tablas y columnas necesarias para el servicio de 
    Traspaso Express existan sin necesidad de migraciones complejas de Alembic en 
    entornos serverless (Vercel). También inicializa el usuario administrador 
    por defecto si no existe.
    
    Returns:
        Tuple[bool, Optional[str]]: (Success status, Error message if any)
    """
    error_msg = None
    try:
        from sqlalchemy import text
        models.Base.metadata.create_all(bind=engine)
        
        # Parche de esquema manual para evitar Error 500 - Ejecución atómica por columna
        all_cols = {
            "tramites": [
                ("radicado_sim", "VARCHAR(100)"),
                ("documentos_json", "TEXT"),
                ("notas", "TEXT")
            ],
            "motos": [
                ("commission_fee", "FLOAT DEFAULT 0.0"),
                ("commission_type", "VARCHAR(20) DEFAULT 'fixed'"),
                ("commission_paid", "BOOLEAN DEFAULT FALSE"),
                ("placa", "VARCHAR(10)"),
                ("nro_motor", "VARCHAR(50)"),
                ("nro_chasis", "VARCHAR(50)")
            ],
            "usuarios": [
                ("telefono", "VARCHAR(20)"),
                ("rol", "VARCHAR(20) DEFAULT 'usuario'"),
                ("tipo_cuenta", "VARCHAR(20) DEFAULT 'natural'"),
                ("cedula", "VARCHAR(20)")
            ]
        }

        from sqlalchemy import text
        for table, cols in all_cols.items():
            for col_name, col_type in cols:
                # Cada columna se intenta en una conexión/transacción separada
                with engine.connect() as conn:
                    try:
                        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col_name} {col_type}"))
                        conn.commit()
                    except Exception:
                        pass # Si la columna ya existe o falla, seguimos con la siguiente
        
        db = SessionLocal()
        email = "brayanpd23@gmail.com"
        user = db.query(models.Usuario).filter(models.Usuario.email == email).first()
        
        # Security Patch: Use environment variables for the initial admin password
        admin_pass = os.environ.get("ADMIN_PASSWORD", "KumbaloAdmin2026#Secure!")
        
        if not user:
            new_admin = models.Usuario(
                nombre="Director Kumbalo",
                email=email,
                hashed_password=pwd_context.hash(admin_pass),
                rol="admin",
                tipo_cuenta="concesionario",
                is_pro=True
            )
            db.add(new_admin)
            db.commit()
        elif user.rol != "admin":
            user.rol = "admin"
            db.commit()
        db.close()
        return True, None
    except Exception as e:
        error_msg = str(e)
        print(f"[SYNC_ERROR] {error_msg}")
        return False, error_msg

@app.on_event("startup")
def on_startup():
    from .database import SessionLocal, engine
    from . import models
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        sync_db_schema(engine, models, SessionLocal, pwd_context)
    except ImportError:
        print("[WARN] Passlib/Bcrypt not found. Admin setup skipped.")
        return

# --- Hardened CORS (Hacker Guardian Lockdown) ---
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://kumbalo.com",
    "https://www.kumbalo.com",
    "https://kumbalo-marketplace.vercel.app",
    "https://kumbalo-api.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*-severlansdevs-projects\.vercel\.app", # Permitir Vercel Previews
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
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
try:
    from .routers import debug
    app.include_router(debug.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load debug router: {e}")

@app.get("/")
def read_root():
    return {"message": "Bienvenido al API del Marketplace de Motos (Fullstack Edition)"}

@app.get("/api/health")
@app.get("/health")
async def health_check():
    """
    Endpoint de salud para monitoreo y verificación de estado en Vercel/Docker.
    """
    return {
        "status": "healthy",
        "service": "kumbalo-api",
        "version": "1.1.0",
        "environment": "production" if os.environ.get("VERCEL") else "local"
    }

# --- Routers (Standardized with /api prefix) ---
try:
    from .routers import auth
    app.include_router(auth.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load auth router: {e}")

try:
    from .routers import motos
    app.include_router(motos.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load motos router: {e}")

try:
    from .routers import mensajes
    app.include_router(mensajes.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load mensajes router: {e}")

try:
    from .routers import payments
    app.include_router(payments.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load payments router: {e}")

try:
    from .routers import chat
    app.include_router(chat.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load chat router: {e}")

try:
    from .routers import telegram
    app.include_router(telegram.router, prefix="/api")
except Exception as e:
    print(f"[ERROR] Could not load telegram router: {e}")

try:
    from .routers import agents
    app.include_router(agents.router, prefix="/api/v1")
except Exception as e:
    print(f"[ERROR] Could not load agents router: {e}")

try:
    from .routers import tramites
    app.include_router(tramites.router, prefix="/api/v1")
except Exception as e:
    print(f"[ERROR] Could not load tramites router: {e}")

try:
    from .routers import runt
    app.include_router(runt.router, prefix="/api/v1/runt", tags=["RUNT Lead Magnet"])
except Exception as e:
    print(f"[WARN] Could not load runt router: {e}")

try:
    from .routers import analytics
    app.include_router(analytics.router, prefix="/api", tags=["Market Intelligence"])
except Exception as e:
    print(f"[WARN] Could not load analytics router: {e}")

# --- Frontend Serving (Static Files) ---
# Se monta al final para que no interfiera con las rutas de /api
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/", StaticFiles(directory=frontend_path, html=True), name="frontend")
else:
    print(f"⚠️ [WARN] Frontend directory not found at {frontend_path}")
