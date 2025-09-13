import asyncio, os
from datetime import datetime, timedelta, timezone
from sqlalchemy import delete
from app.db import SessionLocal
from app.models import IdempotencyKey

TTL_HOURS = int(os.getenv("IDEMP_TTL_HOURS", "24"))


async def cleanup_idempotency_keys():
    while True:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=TTL_HOURS)
        with SessionLocal() as db:
            db.execute(delete(IdempotencyKey).where(IdempotencyKey.created_at < cutoff))
            db.commit()
        await asyncio.sleep(3600)
