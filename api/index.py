import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Añadir la raíz del proyecto al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Crear la aplicación directamente en este archivo (Vercel lo requiere así para máxima compatibilidad)
app = FastAPI(title="KUMBALO API - Vercel Native")

# CORS (Copiado de backend/main.py para consistencia)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Importar y registrar los routers de forma aislada
try:
    from backend.limiter import limiter
    app.state.limiter = limiter
except Exception:
    pass

try:
    from backend.routers import runt
    app.include_router(runt.router, prefix="/api/v1/runt", tags=["RUNT Lead Magnet"])
except Exception as e:
    app.state.runt_error = str(e)

try:
    from backend.routers import auth, motos, payments, tramites, debug, analytics
    from backend.main import sync_db_schema
    from backend.database import SessionLocal, engine
    from backend import models
    from passlib.context import CryptContext
    
    # Ejecutar sicronización de BD (Parche de esquema para Traspaso Express)
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    success, error_msg = sync_db_schema(engine, models, SessionLocal, pwd_context)
    app.state.sync_status = "SUCCESS" if success else "FAILED"
    app.state.sync_error = error_msg
    
    app.include_router(auth.router, prefix="/api")
    app.include_router(motos.router, prefix="/api")
    app.include_router(payments.router, prefix="/api")
    app.include_router(tramites.router, prefix="/api")
    app.include_router(debug.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
except Exception as e:
    import traceback
    app.state.core_error = f"{str(e)} | Trace: {traceback.format_exc()}"

@app.get("/api/v1/error")
def router_error():
    return {
        "status": "error", 
        "runt_module": getattr(app.state, 'runt_error', 'OK'),
        "core_modules": getattr(app.state, 'core_error', 'OK'),
        "db_sync": getattr(app.state, 'sync_status', 'NOT_RUN'),
        "db_error": getattr(app.state, 'sync_error', None),
        "debug_info": {
            "sys_path": sys.path,
            "cwd": os.getcwd()
        }
    }

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "engine": "Vercel Native Runtime"}
