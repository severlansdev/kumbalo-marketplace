import sys
import os
import traceback

# Add the project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from backend.main import app
except Exception as e:
    # If backend fails to load, create a diagnostic app
    from fastapi import FastAPI, Request
    app = FastAPI(title="KUMBALO API - DIAGNOSTIC MODE")
    _err = str(e)
    _trace = traceback.format_exc()

    @app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
    async def diagnostic(path: str, request: Request):
        return {
            "mode": "diagnostic",
            "error": _err,
            "trace": _trace,
            "hint": "The backend failed to import. Check the trace for missing modules."
        }
