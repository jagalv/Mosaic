"""Database engine and session setup.

A single SQLAlchemy Engine per process; `get_session` yields a Session for
request handlers via FastAPI's dependency injection.
"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings

engine = create_engine(
    get_settings().database_url,
    # Verify a connection is alive before using it (cheap insurance against
    # stale connections, e.g. after the DB container restarts).
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base class for ORM models. No models yet in Milestone 0."""


def get_session() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
