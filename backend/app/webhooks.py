import hmac, hashlib, time, json
from fastapi import APIRouter, Header, HTTPException, Depends, Request
from sqlalchemy.orm import Session
from app.config import settings
from app.db import get_db
from app.models import WebhookEvent, Payout

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


def verify(sig: str, ts: str, raw: bytes) -> None:
    if abs(time.time() - int(ts)) > 300:  # 5 minutes
        raise HTTPException(400, "stale signature")
    mac = hmac.new(
        settings.webhook_secret.encode(), f"{ts}.".encode() + raw, hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(mac, sig):
        raise HTTPException(401, "bad signature")


@router.post("/payments")
async def payments(
    req: Request,
    x_sig: str = Header(alias="x-sig"),
    x_ts: str = Header(alias="x-sig-ts"),
    db: Session = Depends(get_db),
):
    raw = await req.body()
    verify(x_sig, x_ts, raw)
    body = json.loads(raw)
    # idempotent on event_id
    ev = db.query(WebhookEvent).filter_by(event_id=body["event_id"]).first()
    if ev:
        return {"ok": True}  # seen
    db.add(WebhookEvent(event_id=body["event_id"], payload=json.dumps(body)))
    # update payout by provider_ref
    p = db.query(Payout).filter_by(provider_ref=body["payout_ref"]).first()
    if p:
        p.status = body.get("status", p.status)
    db.commit()
    return {"ok": True}
