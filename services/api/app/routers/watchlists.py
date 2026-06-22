"""Watchlist endpoints (Milestone 4b). Isolation is enforced by Postgres RLS via
`get_rls_session`, not by app-level owner checks — a row that isn't yours is
simply invisible, so reads/deletes of someone else's row return 404.

Handlers never commit (see rls.py COMMIT CONTRACT): they `flush` for generated
ids and let the dependency commit once at the end.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.models import Company, User, Watchlist, WatchlistItem
from app.rls import get_rls_session
from app.auth import get_current_user

router = APIRouter(prefix="/watchlists")


class CreateWatchlist(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class AddItem(BaseModel):
    ticker: str = Field(min_length=1, max_length=12)


def _items_for(db: Session, watchlist_id: int) -> list[dict]:
    rows = db.execute(
        select(WatchlistItem, Company.ticker, Company.name)
        .join(Company, Company.cik == WatchlistItem.company_cik)
        .where(WatchlistItem.watchlist_id == watchlist_id)
        .order_by(WatchlistItem.id)
    ).all()
    return [
        {
            "id": item.id,
            "company_cik": item.company_cik,
            "ticker": ticker,
            "name": name,
        }
        for item, ticker, name in rows
    ]


def _wl_out(db: Session, wl: Watchlist) -> dict:
    return {
        "id": wl.id,
        "name": wl.name,
        "created_at": wl.created_at.isoformat() if wl.created_at else None,
        "items": _items_for(db, wl.id),
    }


@router.post("")
def create_watchlist(
    body: CreateWatchlist,
    db: Session = Depends(get_rls_session),
    user: User = Depends(get_current_user),
) -> dict:
    wl = Watchlist(user_id=user.id, name=body.name.strip())
    db.add(wl)
    db.flush()  # assign id within the RLS transaction; dep commits
    return _wl_out(db, wl)


@router.get("")
def list_watchlists(db: Session = Depends(get_rls_session)) -> list[dict]:
    wls = db.scalars(select(Watchlist).order_by(Watchlist.id)).all()
    return [_wl_out(db, wl) for wl in wls]


@router.delete("/{watchlist_id}")
def delete_watchlist(
    watchlist_id: int, db: Session = Depends(get_rls_session)
) -> dict:
    # RLS hides other users' rows -> rowcount 0 -> 404 (never reveals existence).
    res = db.execute(delete(Watchlist).where(Watchlist.id == watchlist_id))
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Watchlist not found")
    return {"ok": True}


@router.post("/{watchlist_id}/items")
def add_item(
    watchlist_id: int,
    body: AddItem,
    db: Session = Depends(get_rls_session),
) -> dict:
    wl = db.scalar(select(Watchlist).where(Watchlist.id == watchlist_id))
    if wl is None:  # not yours / doesn't exist
        raise HTTPException(status_code=404, detail="Watchlist not found")

    company = db.scalar(
        select(Company).where(Company.ticker == body.ticker.upper())
    )
    if company is None:
        raise HTTPException(
            status_code=404, detail=f"Company {body.ticker.upper()} not found"
        )

    exists = db.scalar(
        select(WatchlistItem).where(
            WatchlistItem.watchlist_id == watchlist_id,
            WatchlistItem.company_cik == company.cik,
        )
    )
    if exists is not None:
        raise HTTPException(
            status_code=409, detail="Company already in this watchlist"
        )

    db.add(WatchlistItem(watchlist_id=watchlist_id, company_cik=company.cik))
    db.flush()
    return _wl_out(db, wl)


@router.delete("/{watchlist_id}/items/{item_id}")
def delete_item(
    watchlist_id: int, item_id: int, db: Session = Depends(get_rls_session)
) -> dict:
    res = db.execute(
        delete(WatchlistItem).where(
            WatchlistItem.id == item_id,
            WatchlistItem.watchlist_id == watchlist_id,
        )
    )
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"ok": True}
