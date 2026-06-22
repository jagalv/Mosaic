"""Database engines and session setup.

Two engines, by design (Milestone 4b):

  - ADMIN (`engine` / `SessionLocal`) on DATABASE_URL = the superuser `mosaic`
    role. Used by Alembic, ingestion CLIs, and eval — they need superuser/bulk.
    A superuser BYPASSES row-level security, so the API must NOT use this.
  - APP (`app_engine()` / `AppSessionLocal`) on APP_DATABASE_URL = the
    non-superuser `mosaic_app` role. Every API request runs on this engine, so
    RLS is actually enforced. There is NO fallback to DATABASE_URL — that would
    silently re-open the RLS hole — so the app engine fails fast with a clear
    error if APP_DATABASE_URL is unset.

The app engine is built lazily so importing this module (e.g. from an ingestion
CLI that only needs the admin engine) never requires APP_DATABASE_URL.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

# --- ADMIN engine (superuser; Alembic / ingestion / eval) ---
engine = create_engine(
    get_settings().database_url,
    # Verify a connection is alive before using it (cheap insurance against
    # stale connections, e.g. after the DB container restarts).
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for ORM models."""


# --- APP engine (non-superuser mosaic_app; every API request → RLS enforced) ---
@lru_cache(maxsize=1)
def app_engine() -> Engine:
    url = get_settings().app_database_url
    if not url:
        raise RuntimeError(
            "APP_DATABASE_URL is not set. API requests must run as the "
            "non-superuser 'mosaic_app' role so Postgres RLS is enforced; there "
            "is no fallback to the admin DATABASE_URL (that would bypass RLS). "
            "Set APP_DATABASE_URL in .env (see .env.example)."
        )
    return create_engine(url, pool_pre_ping=True)


@lru_cache(maxsize=1)
def _app_sessionmaker() -> sessionmaker:
    return sessionmaker(
        bind=app_engine(), autoflush=False, expire_on_commit=False
    )


def AppSessionLocal() -> Session:
    """A new Session on the APP engine (mosaic_app role, RLS-enforced)."""
    return _app_sessionmaker()()


def get_session() -> Iterator[Session]:
    """FastAPI dependency — yields an APP-engine (mosaic_app) session."""
    db = AppSessionLocal()
    try:
        yield db
    finally:
        db.close()
