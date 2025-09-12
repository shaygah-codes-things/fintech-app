from sqlalchemy import func, select
from app.models import Payout, IdempotencyKey


def test_idempotent_create_one_row(client, login_cookie, dbs):
    r1 = client.post(
        "/payouts",
        headers={"Idempotency-Key": "k-111", **login_cookie},
        params={"amount": "10.00", "currency": "USD"},
    )
    assert r1.status_code == 200
    body1 = r1.json()
    assert "id" in body1

    r2 = client.post(
        "/payouts",
        headers={"Idempotency-Key": "k-111", **login_cookie},
        params={"amount": "10.00", "currency": "USD"},
    )
    assert r2.status_code == 200

    count = dbs.scalar(select(func.count()).select_from(Payout))
    assert count == 1

    idk = dbs.get(IdempotencyKey, "k-111")
    assert idk is not None
    assert idk.payout_id == body1["id"]
