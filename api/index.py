from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/api/health")
@app.get("/api/v1/health")
def health():
    return {"status": "alive", "service": "kumbalo-api"}

@app.api_route("/api/v1/telegram/webhook", methods=["GET", "POST"])
async def telegram_webhook(request: Request):
    return {"status": "ok", "message": "webhook endpoint active"}

@app.get("/api/{path:path}")
def catch_all(path: str):
    return {"status": "ok", "path": path}
