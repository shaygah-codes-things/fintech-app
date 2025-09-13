from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from uuid import uuid4
import time

from app.config import settings
from app.logging import logger
from app.schemas import ErrorBody
import app.models

# Routers
from app.routers.auth import router as auth_router
from app.routers.payouts import router as payouts_router
from app.webhooks import router as webhook_router

app = FastAPI(title="Fintech Backend")


@app.middleware("http")
async def correlation_and_log(request: Request, call_next):
    cid = request.headers.get("x-correlation-id") or str(uuid4())
    request.state.request_id = cid
    start = time.perf_counter()
    response = None

    try:
        response = await call_next(request)
        return response
    finally:
        dur_ms = int((time.perf_counter() - start) * 1000)
        logger.info(
            "request_completed",
            path=str(request.url),
            method=request.method,
            status=getattr(response, "status_code", 500),
            duration_ms=dur_ms,
            cid=cid,
        )
        if response:
            response.headers["x-correlation-id"] = cid


# CORS
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


# Error Helpers
def _error_response(
    status: int, code: str, msg: str, request: Request, details: dict | None = None
) -> JSONResponse:
    body = ErrorBody(
        error=code,
        message=msg,
        details=jsonable_encoder(details) if details is not None else None,  # 👈
        request_id=getattr(request.state, "request_id", None),
    )
    return JSONResponse(status_code=status, content=body.model_dump())


# Error Handlers
@app.exception_handler(ValidationError)
async def on_validation_error(request: Request, exc: ValidationError):
    return _error_response(
        422, "validation_error", "Invalid request", request, {"errors": exc.errors()}
    )


@app.exception_handler(IntegrityError)
async def on_integrity_error(request: Request, exc: IntegrityError):
    return _error_response(
        409, "conflict", "Request conflicts with existing data", request
    )


@app.exception_handler(Exception)
async def on_unexpected(request: Request, exc: Exception):
    logger.exception("unexpected_error", cid=getattr(request.state, "request_id", None))
    return _error_response(
        500, "internal_error", "An unexpected error occurred", request
    )


@app.exception_handler(HTTPException)
async def on_http_exception(request: Request, exc: HTTPException):
    msg = exc.detail if isinstance(exc.detail, str) else "HTTP error"
    return _error_response(exc.status_code, "http_error", msg, request)


@app.exception_handler(RequestValidationError)
async def on_request_validation_error(request: Request, exc: RequestValidationError):
    return _error_response(
        422, "validation_error", "invalid request", request, {"errors": exc.errors()}
    )


# Mount routers
app.include_router(auth_router)
app.include_router(payouts_router)
app.include_router(webhook_router)


@app.get("/health")
def health():
    return {"status": "ok"}
