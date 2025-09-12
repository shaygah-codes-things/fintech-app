from fastapi import APIRouter, Depends, Request, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal
from app.db import get_db
from app.session import current_user_id
from app.models import Payout, IdempotencyKey
from app.logging import logger
import os, time, random, httpx

router = APIRouter(prefix="/payouts", tags=["payouts"])
MOCK_URL = os.getenv("MOCK_URL", "http://localhost:8081/payouts")


@router.post("")
def create_payout(
    req: Request,
    db: Session = Depends(get_db),
    idemp: str | None = Header(default=None, alias="Idempotency-Key"),
    amount: Decimal = Query(..., gt=0),
    currency: str = Query(..., min_length=3, max_length=3),
):
    uid = current_user_id(req)
    if not idemp:
        raise HTTPException(400, detail="Idempotency-Key header required")

    # Idempotency lookup
    existing = db.get(IdempotencyKey, idemp)
    if existing:
        payout = db.get(Payout, existing.payout_id) if existing.payout_id else None
        if payout:
            return {
                "reused": True,
                "payout": {"id": payout.id, "status": payout.status},
            }
        return {"reused": True}

    # Create payout + link idempotency key (atomic)
    p = Payout(user_id=uid, amount=amount, currency=currency, status="processing")
    db.add(p)
    db.flush()  # ensure p.id is available
    db.add(IdempotencyKey(key=idemp, user_id=uid, payout_id=p.id))
    db.commit()
    logger.info("payout_created", payout_id=p.id, uid=uid)
    if os.getenv("ENV") == "test":
        return {"id": p.id, "status": p.status}

    # Call mock provider with retries (bounded exponential + jitter)
    attempts = 0
    while attempts < 4:
        attempts += 1
        try:
            headers = {"x-correlation-id": req.headers.get("x-correlation-id", "")}
            payload = {
                "amount": str(amount),
                "currency": currency,
                "reference": f"payout_{p.id}",
            }
            r = httpx.post(MOCK_URL, json=payload, headers=headers, timeout=5)
            if r.status_code == 200:
                ref = r.json().get("reference")
                if ref:
                    p.provider_ref = ref
                    db.commit()
                    logger.info(
                        "payout_provider_ref_set", payout_id=p.id, provider_ref=ref
                    )
                break
            if r.status_code in (429, 500):
                _sleep_backoff(attempts)
                continue
            r.raise_for_status()
        except Exception as e:
            logger.info("payout_provider_call_error", err=str(e), attempt=attempts)
            _sleep_backoff(attempts)
            continue

    return {"id": p.id, "status": p.status}


@router.get("")
def list_payouts(
    req: Request,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    uid = current_user_id(req)

    base = db.query(Payout).filter(Payout.user_id == uid)
    total = db.query(func.count()).select_from(base.subquery()).scalar()

    items = (
        base.order_by(Payout.id.desc()).offset((page - 1) * limit).limit(limit).all()
    )

    return {
        "page": page,
        "limit": limit,
        "total": int(total or 0),
        "items": [
            {
                "id": i.id,
                "amount": str(i.amount),
                "currency": i.currency,
                "status": i.status,
            }
            for i in items
        ],
    }


def _sleep_backoff(attempt: int):
    # bounded exponential + jitter
    base = min(5.0, 0.5 * (2**attempt))
    time.sleep(base + random.random() * 0.25)
