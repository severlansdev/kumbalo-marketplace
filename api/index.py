import sys
import os
import traceback

# Add the project root to sys.path to allow imports from 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.main import app
except Exception as e:
    from fastapi import FastAPI
    app = FastAPI()
    error_trace = traceback.format_exc()
    @app.get("/api/health")
    @app.get("/api/v1/health")
    @app.get("/api/v1/telegram/webhook")
    def error_diag():
        return {"error": str(e), "trace": error_trace}
