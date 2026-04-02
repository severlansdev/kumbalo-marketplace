import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Añadir la raíz del proyecto al sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Crear la aplicación directamente en este archivo (Vercel lo requiere así para máxima compatibilidad)
app = FastAPI(title="KUMBALO API - Vercel Native")

# CORS Hardened (Hacker Guardian - Sincronizado con main.py)
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
    allow_origin_regex=r"https://.*-severlansdevs-projects\.vercel\.app", # Soporte Vercel Previews
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept"],
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
    
    # Ejecutar sincronización de BD (Cachear resultado para evitar retraso)
    if not getattr(app.state, 'db_synced', False):
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        success, error_msg = sync_db_schema(engine, models, SessionLocal, pwd_context)
        
        # --- AUTO-HEALER: Reparar imágenes negras (Yamaha, Ducati, BMW, Kawasaki, KTM) ---
        if success:
            try:
                db_fix = SessionLocal()
                # 1. Reparar Portadas (Tabla Moto)
                db_fix.query(models.Moto).filter(models.Moto.marca.ilike("%Yamaha%")).update({"image_url": "/assets/motos/yamaha.png"})
                db_fix.query(models.Moto).filter(models.Moto.marca.ilike("%Ducati%")).update({"image_url": "/assets/motos/ducati.png"})
                db_fix.query(models.Moto).filter(models.Moto.marca.ilike("%BMW%")).update({"image_url": "/assets/motos/bmw.png"})
                db_fix.query(models.Moto).filter(models.Moto.marca.ilike("%Kawasaki%")).update({"image_url": "/assets/motos/kawasaki.png"})
                
                # 2. Reparar Galería (Tabla MotoImagen) - Crucial para la vista de detalles
                # Buscamos imágenes que fallen (Unsplash o S3 local rotos)
                broken_yamahas = db_fix.query(models.MotoImagen).join(models.Moto).filter(models.Moto.marca.ilike("%Yamaha%")).all()
                for img in broken_yamahas: img.url = "/assets/motos/yamaha.png"
                
                broken_ducatis = db_fix.query(models.MotoImagen).join(models.Moto).filter(models.Moto.marca.ilike("%Ducati%")).all()
                for img in broken_ducatis: img.url = "/assets/motos/ducati.png"
                
                broken_bmws = db_fix.query(models.MotoImagen).join(models.Moto).filter(models.Moto.marca.ilike("%BMW%")).all()
                for img in broken_bmws: img.url = "/assets/motos/bmw.png"
                
                db_fix.commit()
                db_fix.close()
                print("DATABASE AUTO-HEAL: Portfolio AND Gallery repointed to local assets.")
            except Exception as e:
                import traceback
                print(f"DATABASE AUTO-HEAL FAILED: {str(e)} | {traceback.format_exc()}")
        
        app.state.sync_status = "SUCCESS" if success else "FAILED"
        app.state.db_synced = success
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
