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
# Si un módulo falla (ej. por una importación faltante), los demás siguen funcionando.
try:
    from backend.routers import runt
    app.include_router(runt.router, prefix="/api/v1/runt", tags=["RUNT Lead Magnet"])
except Exception as e:
    app.state.runt_error = str(e)

try:
    from backend.routers import auth, motos, payments
    app.include_router(auth.router, prefix="/api")
    app.include_router(motos.router, prefix="/api")
    app.include_router(payments.router, prefix="/api")
except Exception as e:
    app.state.core_error = str(e)

@app.get("/api/v1/error")
def router_error():
    return {
        "status": "error", 
        "runt_module": getattr(app.state, 'runt_error', 'OK'),
        "core_modules": getattr(app.state, 'core_error', 'OK')
    }

@app.get("/api/v1/health")
def health():
    return {"status": "healthy", "engine": "Vercel Native Runtime"}
