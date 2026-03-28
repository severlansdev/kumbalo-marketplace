import sys
import os

# Añadir la raíz del proyecto al sys.path para que los imports funcionen en Vercel
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar la app de FastAPI desde el core del backend
# Es CRÍTICO que 'app' esté definida en el nivel superior para que el builder de Vercel la encuentre.
try:
    from backend.main import app
except ImportError as e:
    # Fallback por si hay un error de importación crítico
    from fastapi import FastAPI
    app = FastAPI(title="KUMBALO API - ERROR LOADING BACKEND")
    
    @app.get("/")
    def error():
        return {"status": "error", "message": str(e)}

# El objeto 'app' ahora es visible directamente para Vercel.
