from fastapi import APIRouter, Depends, Request, Response, HTTPException, Header, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from decimal import Decimal
import os, time, random, httpx
from sqlalchemy.exc import IntegrityError

from app.db import get_db
from app.session import current_user_id, set_user_on_request
from app.models import Payout, IdempotencyKey
from app.logging import logger
from app.schemas import CreatePayoutRequest, PayoutOut, Page
from app.rate_limit import limiter

router = APIRouter(prefix="/payouts", tags=["payouts"])
MOCK_URL = os.getenv("MOCK_URL", "http://localhost:8081/payouts")


@router.post(
    "",
    response_model=PayoutOut,
    dependencies=[Depends(set_user_on_request)],
)
@limiter.limit("5/minute")
def create_payout(
    body: CreatePayoutRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    idemp: str | None = Header(default=None, alias="Idempotency-Key"),
):
    uid = current_user_id(request)
    if not idemp:
        raise HTTPException(400, detail="Idempotency-Key header required")

    # Try to claim the idempotency key FIRST (no payout yet).
    # If we win (rowcount==1), we own the key for this window.
    # If we lose (rowcount==0), someone else already claimed it.
    stmt = (
        insert(IdempotencyKey)
        .values(key=idemp, user_id=uid, payout_id=None)
        .on_conflict_do_nothing(index_elements=[IdempotencyKey.key])
    )
    res = db.execute(stmt)
    db.flush()

    if res.rowcount == 0:
        # Another request already claimed this key.
        # If its payout_id is set, return that payout.
        # If not yet set, briefly wait for the winner to finish.
        deadline = time.time() + 3.0  # wait up to 3s
        while time.time() < deadline:
            existing = db.get(IdempotencyKey, idemp)
            if existing and existing.payout_id:
                payout = db.get(Payout, existing.payout_id)
                return PayoutOut(
                    id=payout.id,
                    amount=str(payout.amount),
                    currency=payout.currency,
                    status=payout.status,
                )
            time.sleep(0.05)
        # Still no payout_id; report "processing" (client can retry).
        raise HTTPException(409, detail="Idempotency key currently processing")

    # Create payout
    p = Payout(
        user_id=uid,
        amount=str(body.amount),
        currency=body.currency,
        status="processing",
    )
    db.add(p)
    db.flush()

    # Back-fill payout_id on the key and commit
    db.query(IdempotencyKey).filter(IdempotencyKey.key == idemp).update(
        {"payout_id": p.id}
    )
    db.commit()
    logger.info("payout_created", payout_id=p.id, uid=uid)

    if os.getenv("ENV") == "test":
        return PayoutOut(
            id=p.id, amount=str(p.amount), currency=p.currency, status=p.status
        )

    # Call mock provider with retries (bounded exponential + jitter)
    attempts = 0
    while attempts < 4:
        attempts += 1
        try:
            headers = {"x-correlation-id": request.headers.get("x-correlation-id", "")}
            payload = {
                "amount": str(body.amount),
                "currency": body.currency,
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

    return PayoutOut(
        id=p.id, amount=str(p.amount), currency=p.currency, status=p.status
    )


@router.get(
    "",
    response_model=Page[PayoutOut],
    dependencies=[Depends(set_user_on_request)],
)
@limiter.limit("60/minute")  # per-user
def list_payouts(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
):
    uid = current_user_id(request)
    base = db.query(Payout).filter(Payout.user_id == uid)
    total = db.query(func.count()).select_from(base.subquery()).scalar()
    items = (
        base.order_by(Payout.id.desc()).offset((page - 1) * limit).limit(limit).all()
    )

    return Page[PayoutOut](
        page=page,
        limit=limit,
        total=int(total or 0),
        items=[
            PayoutOut(
                id=i.id,
                amount=str(i.amount),
                currency=i.currency,
                status=i.status,
            )
            for i in items
        ],
    )


def _sleep_backoff(attempt: int):
    base = min(5.0, 0.5 * (2**attempt))
    time.sleep(base + random.random() * 0.25)
