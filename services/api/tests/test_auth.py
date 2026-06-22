"""Auth endpoint tests (Milestone 4a) — offline.

Uses an in-memory SQLite DB (only the `users` table) via a `get_session`
dependency override, so the suite stays DB-free and fast like the rest of the
tests. Covers signup, duplicate-email, password length, login (ok / wrong-pw /
unknown-email), /me (authed / unauthed), and logout.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import get_session
from app.main import app
from app.models import User

# Single shared in-memory connection (StaticPool) so the DB persists across
# sessions within a test.
_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
_TestSession = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)


def _override_session():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_session] = _override_session

GOOD = {"email": "Alice@Example.com", "password": "correct horse battery"}


@pytest.fixture
def client():
    # Fresh `users` table per test for isolation.
    User.__table__.drop(_engine, checkfirst=True)
    User.__table__.create(_engine)
    with TestClient(app) as c:
        yield c


def test_signup_ok_sets_cookie(client):
    r = client.post("/auth/signup", json=GOOD)
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["email"] == "alice@example.com"  # normalized to lower-case
    assert isinstance(body["id"], int)
    assert client.cookies.get("mosaic_session")


def test_signup_duplicate_email_409(client):
    assert client.post("/auth/signup", json=GOOD).status_code == 200
    client.cookies.clear()
    r = client.post(
        "/auth/signup",
        json={"email": "alice@example.com", "password": "another good one"},
    )
    assert r.status_code == 409


def test_signup_short_password_rejected(client):
    r = client.post(
        "/auth/signup", json={"email": "bob@example.com", "password": "short"}
    )
    assert r.status_code == 422


def test_login_ok(client):
    client.post("/auth/signup", json=GOOD)
    client.cookies.clear()
    r = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": GOOD["password"]},
    )
    assert r.status_code == 200
    assert client.cookies.get("mosaic_session")


def test_login_wrong_password_401(client):
    client.post("/auth/signup", json=GOOD)
    client.cookies.clear()
    r = client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "not-the-password"},
    )
    assert r.status_code == 401


def test_login_unknown_email_is_same_401(client):
    # No user enumeration: unknown email looks identical to a wrong password.
    r = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "whatever12345"},
    )
    assert r.status_code == 401


def test_me_authed_ok(client):
    client.post("/auth/signup", json=GOOD)  # signup auto-sets the cookie
    r = client.get("/auth/me")
    assert r.status_code == 200
    assert r.json()["email"] == "alice@example.com"


def test_me_unauthed_401(client):
    r = client.get("/auth/me")
    assert r.status_code == 401


def test_logout_clears_session(client):
    client.post("/auth/signup", json=GOOD)
    assert client.get("/auth/me").status_code == 200
    client.post("/auth/logout")
    assert client.get("/auth/me").status_code == 401
