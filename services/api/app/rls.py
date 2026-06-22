"""Request-scoped DB session with row-level security context (Milestone 4b).

`get_rls_session` composes `get_current_user` with a fresh session that sets the
Postgres GUC `app.current_user_id` for the request's transaction, so every query
is filtered by the RLS policies (migration 0007) — isolation enforced by the DB,
not app code.

COMMIT CONTRACT (load-bearing): this dependency is the SOLE committer. The GUC is
set with `is_local => true`, so it lives only for the current transaction — a
mid-handler commit would END that transaction and CLEAR the GUC, silently
breaking isolation for the rest of the request. Handlers must NOT commit; they
flush if they need a generated id, and this dep commits once at the end.
"""

from collections.abc import Iterator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import AppSessionLocal
from app.models import User


def get_rls_session(
    user: User = Depends(get_current_user),
) -> Iterator[Session]:
    db = AppSessionLocal()
    try:
        # set_config(..., is_local => true) == SET LOCAL, but parameter-safe
        # (SET LOCAL can't bind). Autobegins the transaction the GUC is scoped to.
        db.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user.id)},
        )
        yield db
        db.commit()  # sole commit for the request
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
