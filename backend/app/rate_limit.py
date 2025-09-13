from __future__ import annotations
import os
from typing import Optional
from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address


def _get_user_id(request: Request) -> Optional[str]:
    return str(getattr(request.state, "user_id", "") or "")


def key_per_user(request: Request) -> str:
    uid = _get_user_id(request)
    return f"user:{uid}" if uid else f"ip:{get_remote_address(request)}"


def key_per_ip(request: Request) -> str:
    return f"ip:{get_remote_address(request)}"


def build_limiter() -> Limiter:
    storage_uri = os.getenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/0")
    return Limiter(
        key_func=key_per_user,  # default per-user
        storage_uri=storage_uri,
        headers_enabled=True,
    )


limiter = build_limiter()
