def test_401_requires_auth(client):
    r = client.get("/payouts")
    assert r.status_code == 401
    body = r.json()
    assert "error" in body and "request_id" in body


def test_400_missing_idempotency(login_cookie, client):
    r = client.post(
        "/payouts", json={"amount": "10.00", "currency": "USD"}, headers=login_cookie
    )
    assert r.status_code == 400
    body = r.json()
    assert body["error"] in {"http_error", "validation_error"}


def test_422_invalid_currency(login_cookie, client):
    r = client.post(
        "/payouts",
        json={"amount": "10.00", "currency": "ZZZ"},
        headers={"Idempotency-Key": "k-xyz", **login_cookie},
    )
    assert r.status_code == 422
    assert "validation_error" in r.text
