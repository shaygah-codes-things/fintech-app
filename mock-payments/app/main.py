from fastapi import FastAPI, BackgroundTasks, Request
import os, time, random, json, hmac, hashlib, httpx

app = FastAPI(title="Mock Payments")

WEBHOOK = os.getenv("WEBHOOK_TARGET", "http://localhost:8000/webhooks/payments")
SECRET = os.getenv("WEBHOOK_SHARED_SECRET", "changeme")


def send_webhook(payout_ref: str, cid: str | None):
    time.sleep(random.choice([1, 2, 3]))  # pretend to process
    payload = {
        "event_id": f"evt_{int(time.time()*1000)}_{random.randint(100,999)}",
        "payout_ref": payout_ref,
        "status": random.choice(["paid", "failed"]),
    }
    raw = json.dumps(payload).encode()
    ts = str(int(time.time()))
    sig = hmac.new(SECRET.encode(), f"{ts}.".encode() + raw, hashlib.sha256).hexdigest()
    headers = {"x-sig-ts": ts, "x-sig": sig}
    if cid:
        headers["x-correlation-id"] = cid
    try:
        httpx.post(
            WEBHOOK,
            content=raw,
            headers={"content-type": "application/json", **headers},
            timeout=5,
        )

    except Exception:
        pass


@app.post("/payouts")
async def create(req: Request, bg: BackgroundTasks):
    body = await req.json()
    # Simulate transient errors (20% 429, 10% 500)
    r = random.random()
    if r < 0.2:
        return {"error": "rate_limited"}, 429
    if r < 0.3:
        return {"error": "server"}, 500

    ref = f"mock_{int(time.time()*1000)}"
    bg.add_task(send_webhook, ref, req.headers.get("x-correlation-id"))
    return {"reference": ref}
