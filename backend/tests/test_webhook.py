import hmac, hashlib, json, time
from sqlalchemy import select
from app.models import Payout

SECRET = "test_secret"


def sign(ts: str, raw: str) -> str:
    return hmac.new(SECRET.encode(), f"{ts}.{raw}".encode(), hashlib.sha256).hexdigest()


def test_webhook_updates_status(client, login_cookie, dbs):
    r = client.post(
        "/payouts",
        headers={"Idempotency-Key": "k-222", **login_cookie},
        json={"amount": "25.00", "currency": "USD"},
    )
    assert r.status_code == 200
    pid = r.json()["id"]

    p = dbs.get(Payout, pid)
    assert p is not None
    p.provider_ref = f"payout_{pid}"
    dbs.commit()

    payload = {
        "event_id": "evt_test_1",
        "payout_ref": f"payout_{pid}",
        "status": "paid",
    }
    raw = json.dumps(payload)
    ts = str(int(time.time()))
    sig = sign(ts, raw)
    r2 = client.post(
        "/webhooks/payments",
        data=raw,
        headers={"x-sig-ts": ts, "x-sig": sig, "content-type": "application/json"},
    )
    assert r2.status_code in (200, 204)

    st = dbs.scalar(select(Payout.status).where(Payout.id == pid))
    assert st == "paid"


def test_webhook_rejects_bad_signature(client, login_cookie, dbs):
    r = client.post(
        "/payouts",
        headers={"Idempotency-Key": "k-333", **login_cookie},
        json={"amount": "15.00", "currency": "USD"},
    )
    pid = r.json()["id"]

    p = dbs.get(Payout, pid)
    assert p is not None
    p.provider_ref = f"payout_{pid}"
    dbs.commit()

    payload = {
        "event_id": "evt_test_2",
        "payout_ref": f"payout_{pid}",
        "status": "paid",
    }
    raw = json.dumps(payload)
    ts = str(int(time.time()))
    bad_sig = "deadbeef"
    r2 = client.post(
        "/webhooks/payments",
        data=raw,
        headers={"x-sig-ts": ts, "x-sig": bad_sig, "content-type": "application/json"},
    )
    assert r2.status_code in (400, 401, 403)

    st = dbs.scalar(select(Payout.status).where(Payout.id == pid))
    assert st == "processing"
