import sys
import os
import traceback

# Add the project root to sys.path to allow imports from 'backend'
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.main import app
except Exception as e:
    from fastapi import FastAPI, Request
    app = FastAPI()
    error_trace = traceback.format_exc()
    @app.api_route("/api/health", methods=["GET", "POST"])
    @app.api_route("/api/v1/health", methods=["GET", "POST"])
    @app.api_route("/api/v1/telegram/webhook", methods=["GET", "POST"])
    def error_diag(request: Request):
        return {"error": str(e), "trace": error_trace}
