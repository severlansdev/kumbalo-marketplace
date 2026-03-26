import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from .database import engine, Base
from . import models
from .limiter import limiter
from .logging_config import logger, log_request

# Crear tablas en DB si no existen
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="KUMBALO API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Instrument FastAPI with Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Configurar CORS para permitir comunicación local y prevenir bypass
origins = [
    "http://localhost",
    "http://127.0.0.1",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    log_request(request.method, str(request.url.path), response.status_code, duration_ms)
    return response

@app.get("/")
def read_root():
    return {"message": "🚀 Bienvenido al API del Marketplace de Motos (Fullstack Edition)"}


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "kumbalo-api",
        "version": "1.0.0"
    }

from .routers import auth, motos, mensajes, payments, chat, runt

app.include_router(auth.router)
app.include_router(motos.router)
app.include_router(mensajes.router)
app.include_router(payments.router)
app.include_router(chat.router)
app.include_router(runt.router, prefix="/api/v1/runt", tags=["RUNT Lead Magnet"])
