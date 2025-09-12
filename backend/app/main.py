from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from uuid import uuid4

from app.config import settings
from app.logging import logger
import app.models

# Routers
from app.routers.auth import router as auth_router
from app.routers.payouts import router as payouts_router
from app.webhooks import router as webhook_router

app = FastAPI(title="Fintech Backend")


@app.middleware("http")
async def correlation(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or str(uuid4())
    response = await call_next(request)
    response.headers["x-correlation-id"] = cid
    logger.info(
        "request_completed",
        path=str(request.url),
        method=request.method,
        status=response.status_code,
        cid=cid,
    )
    return response


origins = (
    [o.strip() for o in settings.cors_origins.split(",")]
    if isinstance(settings.cors_origins, str)
    else settings.cors_origins
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount routers
app.include_router(auth_router)
app.include_router(payouts_router)
app.include_router(webhook_router)


@app.get("/health")
def health():
    return {"status": "ok"}
