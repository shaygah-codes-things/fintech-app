import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import uuid

# test env
os.environ["WEBHOOK_SHARED_SECRET"] = "test_secret"
os.environ["ENV"] = "test"

from app.main import app as fastapi_app
from app.db import Base, get_db
import app.models

TEST_DB_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(
    TEST_DB_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)
TestingSessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


@pytest.fixture(scope="function", autouse=True)
def _create_schema():
    Base.metadata.create_all(bind=engine)
    try:
        yield
    finally:
        Base.metadata.drop_all(bind=engine)


def _override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


fastapi_app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def client(_create_schema):
    return TestClient(fastapi_app)


@pytest.fixture
def dbs():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def login_cookie(client):
    # unique user per test to isolate rate-limit counters
    email = f"test+{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/auth/test-login", params={"email": email})
    assert r.status_code == 200
    return {"Cookie": f"session={client.cookies.get('session')}"}
