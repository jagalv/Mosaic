"""Cross-user RLS security test (Milestone 4b) — the deliverable that matters.

RLS can't be exercised on SQLite, so this runs against the local Postgres and is
skipped if none is reachable (the rest of the suite stays offline/green). Proves,
at BOTH levels, that user A can never read or write user B's data:
  - DB level: with the GUC set to B, A's rows are invisible and un-writable; an
    unset/empty GUC matches nothing (fail-closed); a fresh connection has no GUC
    (no pooling leak).
  - API level: A's session can't see or delete B's watchlist (404, never B's data).
Plus a multi-statement request under RLS (proves the commit contract — the GUC
stays live for the whole request).
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.db import AppSessionLocal, app_engine, engine, get_session
from app.main import app


def _pg_available() -> bool:
    # Must connect AS mosaic_app (the APP engine) — that's the role RLS binds to.
    # Skips if the DB is down, the role/grants are missing, or APP_DATABASE_URL
    # is unset.
    try:
        with app_engine().connect() as c:
            c.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _pg_available(), reason="requires local Postgres (docker compose up)"
)


def _cleanup_users(emails: list[str]) -> None:
    # users has no RLS; FK ON DELETE CASCADE removes their watchlists/items.
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM users WHERE email = ANY(:e)"), {"e": emails}
        )


@pytest.fixture
def pg_app():
    """Point get_session at the real Postgres for the duration of the test
    (self-contained; does not depend on any other test module's override)."""
    def _app_session():
        db = AppSessionLocal()  # mosaic_app role -> RLS enforced
        try:
            yield db
        finally:
            db.close()

    prev = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = _app_session
    try:
        yield app
    finally:
        if prev is not None:
            app.dependency_overrides[get_session] = prev
        else:
            app.dependency_overrides.pop(get_session, None)


# ---- DB-level: policies + fail-closed + no pooling leak ----

def test_rls_db_level_isolation_and_fail_closed():
    conn = app_engine().connect()  # connect AS mosaic_app, not admin
    trans = conn.begin()
    try:
        a = conn.execute(
            text(
                "INSERT INTO users (email, password_hash) "
                "VALUES ('rlsdb-a@mosaic.test', 'x') RETURNING id"
            )
        ).scalar()
        b = conn.execute(
            text(
                "INSERT INTO users (email, password_hash) "
                "VALUES ('rlsdb-b@mosaic.test', 'x') RETURNING id"
            )
        ).scalar()

        # As A: create a watchlist, see exactly one.
        conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(a)})
        wid = conn.execute(
            text("INSERT INTO watchlists (user_id, name) VALUES (:u, 'A') RETURNING id"),
            {"u": a},
        ).scalar()
        assert conn.execute(text("SELECT count(*) FROM watchlists")).scalar() == 1

        # As B: A's row is invisible and cannot be updated or deleted.
        conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(b)})
        assert conn.execute(text("SELECT count(*) FROM watchlists")).scalar() == 0
        assert conn.execute(
            text("UPDATE watchlists SET name = 'hacked' WHERE id = :i"), {"i": wid}
        ).rowcount == 0
        assert conn.execute(
            text("DELETE FROM watchlists WHERE id = :i"), {"i": wid}
        ).rowcount == 0

        # Fail-closed: unset/empty GUC -> no rows (never errors, never allow-all).
        conn.execute(text("SELECT set_config('app.current_user_id', '', true)"))
        assert conn.execute(text("SELECT count(*) FROM watchlists")).scalar() == 0
    finally:
        trans.rollback()  # discard all test rows
        conn.close()

    # No pooling leak: a fresh connection/txn has never seen the GUC.
    with engine.connect() as conn2:
        leaked = conn2.execute(
            text("SELECT current_setting('app.current_user_id', true)")
        ).scalar()
        assert leaked in (None, "")


# ---- API-level: A cannot see or delete B's watchlist ----

def test_api_cross_user_isolation(pg_app):
    emails = ["rlsapi-a@mosaic.test", "rlsapi-b@mosaic.test"]
    _cleanup_users(emails)
    try:
        ca, cb = TestClient(app), TestClient(app)
        assert ca.post("/auth/signup", json={"email": emails[0], "password": "password-a-1"}).status_code == 200
        assert cb.post("/auth/signup", json={"email": emails[1], "password": "password-b-1"}).status_code == 200

        wa = ca.post("/watchlists", json={"name": "A list"}).json()
        wb = cb.post("/watchlists", json={"name": "B list"}).json()

        ids_a = {w["id"] for w in ca.get("/watchlists").json()}
        ids_b = {w["id"] for w in cb.get("/watchlists").json()}
        assert wa["id"] in ids_a and wb["id"] not in ids_a
        assert wb["id"] in ids_b and wa["id"] not in ids_b

        # B can't delete or write A's watchlist -> 404 (never B's data, never A's).
        assert cb.delete(f"/watchlists/{wa['id']}").status_code == 404
        assert cb.post(f"/watchlists/{wa['id']}/items", json={"ticker": "AAPL"}).status_code == 404
        # A still owns it.
        assert wa["id"] in {w["id"] for w in ca.get("/watchlists").json()}
        # A can delete its own.
        assert ca.delete(f"/watchlists/{wa['id']}").status_code == 200
    finally:
        _cleanup_users(emails)


# ---- Commit contract: multi-statement request keeps the GUC live ----

def test_multi_statement_request_under_rls(pg_app):
    email = "rlsapi-multi@mosaic.test"
    _cleanup_users([email])
    try:
        c = TestClient(app)
        assert c.post("/auth/signup", json={"email": email, "password": "password-1"}).status_code == 200
        wl = c.post("/watchlists", json={"name": "multi"}).json()

        # add_item runs several statements (incl. an INSERT whose WITH CHECK
        # subqueries watchlists under RLS) in ONE request. Success proves the GUC
        # stayed set the whole time — i.e. no handler self-commit cleared it.
        r = c.post(f"/watchlists/{wl['id']}/items", json={"ticker": "AAPL"})
        assert r.status_code == 200, r.text
        assert any(it["ticker"] == "AAPL" for it in r.json()["items"])

        got = c.get("/watchlists").json()
        assert any(it["ticker"] == "AAPL" for w in got for it in w["items"])
    finally:
        _cleanup_users([email])


# ---- Notes (M4c): same RLS isolation, DB + API ----

def test_rls_notes_db_level():
    conn = app_engine().connect()  # AS mosaic_app
    trans = conn.begin()
    try:
        cik = conn.execute(text("SELECT cik FROM companies LIMIT 1")).scalar()
        if cik is None:
            pytest.skip("no companies ingested")
        a = conn.execute(
            text("INSERT INTO users (email, password_hash) VALUES ('rlsnote-a@mosaic.test','x') RETURNING id")
        ).scalar()
        b = conn.execute(
            text("INSERT INTO users (email, password_hash) VALUES ('rlsnote-b@mosaic.test','x') RETURNING id")
        ).scalar()

        conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(a)})
        nid = conn.execute(
            text("INSERT INTO notes (user_id, body, company_cik) VALUES (:u, 'A note', :c) RETURNING id"),
            {"u": a, "c": cik},
        ).scalar()
        assert conn.execute(text("SELECT count(*) FROM notes")).scalar() == 1

        conn.execute(text("SELECT set_config('app.current_user_id', :u, true)"), {"u": str(b)})
        assert conn.execute(text("SELECT count(*) FROM notes")).scalar() == 0
        assert conn.execute(text("UPDATE notes SET body='hacked' WHERE id=:i"), {"i": nid}).rowcount == 0
        assert conn.execute(text("DELETE FROM notes WHERE id=:i"), {"i": nid}).rowcount == 0

        conn.execute(text("SELECT set_config('app.current_user_id', '', true)"))
        assert conn.execute(text("SELECT count(*) FROM notes")).scalar() == 0
    finally:
        trans.rollback()
        conn.close()


def test_api_cross_user_note_isolation(pg_app):
    emails = ["rlsnote-api-a@mosaic.test", "rlsnote-api-b@mosaic.test"]
    _cleanup_users(emails)
    try:
        ca, cb = TestClient(app), TestClient(app)
        assert ca.post("/auth/signup", json={"email": emails[0], "password": "password-a-1"}).status_code == 200
        assert cb.post("/auth/signup", json={"email": emails[1], "password": "password-b-1"}).status_code == 200

        na = ca.post("/notes", json={"body": "A's private note", "company": "AAPL"})
        assert na.status_code == 200, na.text
        note_id = na.json()["id"]

        # Exactly-one-target validation.
        assert ca.post("/notes", json={"body": "x"}).status_code == 422  # neither
        assert ca.post("/notes", json={"body": "x", "company": "AAPL", "accession": "z"}).status_code == 422  # both

        # B can't see / patch / delete A's note.
        assert note_id not in {n["id"] for n in cb.get("/notes").json()}
        assert cb.patch(f"/notes/{note_id}", json={"body": "hacked"}).status_code == 404
        assert cb.delete(f"/notes/{note_id}").status_code == 404

        # A owns it: visible, editable, deletable.
        assert note_id in {n["id"] for n in ca.get("/notes").json()}
        assert ca.patch(f"/notes/{note_id}", json={"body": "edited"}).status_code == 200
        assert ca.delete(f"/notes/{note_id}").status_code == 200
    finally:
        _cleanup_users(emails)
