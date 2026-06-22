"""Note endpoints (Milestone 4c). Same RLS pattern as watchlists: every query
runs via `get_rls_session` (mosaic_app + the per-request GUC), so a note that
isn't yours is invisible — reads/updates/deletes of it return 404. Handlers
flush for generated ids and never commit (the dep is the sole committer).

Each note targets EXACTLY ONE of a company (by ticker) or a filing (by
accession); the API resolves those to company_cik / filing_id.
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.models import Company, Filing, Note, User
from app.rls import get_rls_session

router = APIRouter(prefix="/notes")


class CreateNote(BaseModel):
    body: str = Field(min_length=1, max_length=10000)
    company: str | None = Field(default=None, max_length=12)
    accession: str | None = Field(default=None, max_length=32)


class UpdateNote(BaseModel):
    body: str = Field(min_length=1, max_length=10000)


def _select_notes():
    return (
        select(Note, Company.ticker, Company.name, Filing.accession_no)
        .outerjoin(Company, Company.cik == Note.company_cik)
        .outerjoin(Filing, Filing.id == Note.filing_id)
    )


def _serialize(row) -> dict:
    note, ticker, name, accession = row
    if note.company_cik is not None:
        target = {
            "type": "company",
            "cik": note.company_cik,
            "ticker": ticker,
            "name": name,
        }
    else:
        target = {
            "type": "filing",
            "filing_id": note.filing_id,
            "accession_no": accession,
        }
    return {
        "id": note.id,
        "body": note.body,
        "created_at": note.created_at.isoformat() if note.created_at else None,
        "updated_at": note.updated_at.isoformat() if note.updated_at else None,
        "target": target,
    }


def _one(db: Session, note_id: int) -> dict:
    row = db.execute(_select_notes().where(Note.id == note_id)).first()
    return _serialize(row)


@router.post("")
def create_note(
    body: CreateNote,
    db: Session = Depends(get_rls_session),
    user: User = Depends(get_current_user),
) -> dict:
    if bool(body.company) == bool(body.accession):
        raise HTTPException(
            status_code=422,
            detail="Provide exactly one target: `company` or `accession`.",
        )

    company_cik = None
    filing_id = None
    if body.company:
        company = db.scalar(
            select(Company).where(Company.ticker == body.company.upper())
        )
        if company is None:
            raise HTTPException(status_code=404, detail="Company not found")
        company_cik = company.cik
    else:
        filing = db.scalar(
            select(Filing).where(Filing.accession_no == body.accession)
        )
        if filing is None:
            raise HTTPException(status_code=404, detail="Filing not found")
        filing_id = filing.id

    note = Note(
        user_id=user.id,
        body=body.body.strip(),
        company_cik=company_cik,
        filing_id=filing_id,
    )
    db.add(note)
    db.flush()  # assign id within the RLS transaction; dep commits
    return _one(db, note.id)


@router.get("")
def list_notes(
    company: str | None = None,
    accession: str | None = None,
    db: Session = Depends(get_rls_session),
) -> list[dict]:
    q = _select_notes()
    if company is not None:
        comp = db.scalar(select(Company).where(Company.ticker == company.upper()))
        if comp is None:
            return []
        q = q.where(Note.company_cik == comp.cik)
    if accession is not None:
        fil = db.scalar(select(Filing).where(Filing.accession_no == accession))
        if fil is None:
            return []
        q = q.where(Note.filing_id == fil.id)
    q = q.order_by(Note.updated_at.desc())
    return [_serialize(r) for r in db.execute(q).all()]


@router.patch("/{note_id}")
def update_note(
    note_id: int,
    body: UpdateNote,
    db: Session = Depends(get_rls_session),
) -> dict:
    note = db.scalar(select(Note).where(Note.id == note_id))  # RLS -> None if not yours
    if note is None:
        raise HTTPException(status_code=404, detail="Note not found")
    note.body = body.body.strip()  # onupdate bumps updated_at on flush
    db.flush()
    return _one(db, note.id)


@router.delete("/{note_id}")
def delete_note(
    note_id: int, db: Session = Depends(get_rls_session)
) -> dict:
    res = db.execute(delete(Note).where(Note.id == note_id))
    if res.rowcount == 0:
        raise HTTPException(status_code=404, detail="Note not found")
    return {"ok": True}
