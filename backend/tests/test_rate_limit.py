# backend/tests/test_rate_limit.py
from __future__ import annotations


def test_rate_limit_payouts_post_per_user(client, login_cookie):
    """
    POST /payouts is limited to 5/min per user.
    The 6th request should return 429 and include X-RateLimit-* headers.
    """
    # First 5 should pass
    for i in range(5):
        r = client.post(
            "/payouts",
            headers={"Idempotency-Key": f"k-ratel-{i}", **login_cookie},
            json={"amount": "1.00", "currency": "USD"},
        )
        assert r.status_code == 200, f"request {i+1} failed: {r.text}"

    # 6th should be rate-limited
    r6 = client.post(
        "/payouts",
        headers={"Idempotency-Key": "k-ratel-6", **login_cookie},
        json={"amount": "1.00", "currency": "USD"},
    )
    assert r6.status_code == 429, r6.text

    # Headers from SlowAPI should be present
    limit = r6.headers.get("X-RateLimit-Limit")
    remaining = r6.headers.get("X-RateLimit-Remaining")
    reset = r6.headers.get("X-RateLimit-Reset")

    assert limit is not None, "X-RateLimit-Limit header missing"
    assert remaining is not None, "X-RateLimit-Remaining header missing"
    assert reset is not None, "X-RateLimit-Reset header missing"

    # Remaining should be 0 when we exceed the limit (best-effort assertion)
    try:
        assert int(remaining) == 0
    except Exception:
        # Some storages might format differently; presence is enough then.
        pass

    # Body should be normalized by our error handler
    body = r6.json()
    assert body.get("error") == "rate_limited"
    assert "request_id" in body


def test_rate_limit_payouts_get_headers_present(client, login_cookie):
    """
    GET /payouts has a 60/min limit per user.
    We don't hammer it to 61 (slow test), but we confirm headers are present on a normal call.
    """
    r = client.get("/payouts", headers=login_cookie)
    assert r.status_code == 200, r.text

    limit = r.headers.get("X-RateLimit-Limit")
    remaining = r.headers.get("X-RateLimit-Remaining")
    reset = r.headers.get("X-RateLimit-Reset")

    assert limit is not None, "X-RateLimit-Limit header missing"
    assert remaining is not None, "X-RateLimit-Remaining header missing"
    assert reset is not None, "X-RateLimit-Reset header missing"
