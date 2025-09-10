from fastapi import FastAPI, Request
from uuid import uuid4

app = FastAPI(title="Fintech Backend")

@app.middleware("http")
async def correlation(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or str(uuid4())
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    return response

@app.get("/")
def home():
    return {"message": "Fintech API is running", "docs": "/docs", "health": "/health"}

@app.get("/health")
def health():
    return {"status": "ok"}
