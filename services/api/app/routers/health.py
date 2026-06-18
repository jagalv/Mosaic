"""Health check endpoint.

This is the entire Milestone 0 demo: it proves the request path
frontend -> FastAPI -> Postgres -> back works. It runs a trivial `SELECT 1`
to confirm real DB connectivity (not just that the API process is up).
"""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import get_session

router = APIRouter()


@router.get("/health")
def health(db: Session = Depends(get_session)) -> dict:
    """Report service and database status.

    Always returns 200 so the frontend can render a status badge either way;
    `db` flips to "error" (with the reason) when the DB is unreachable.
    """
    db_status = "ok"
    detail: str | None = None
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:  # surface the failure to the UI instead of 500ing
        db_status = "error"
        detail = str(exc)

    result = {"service": "ok", "db": db_status}
    if detail:
        result["detail"] = detail
    return result
