"""Document body-text storage seam.

`content_text` persistence is isolated behind DocumentStore so an R2-backed
store can replace the Postgres one later (Phase 2, when the corpus grows)
without touching ingestion, the segmenter, or the API. Section metadata stays
in Postgres regardless.

Today there is exactly one implementation: PostgresDocumentStore (text lives in
filing_documents.content_text). This is the single sanctioned abstraction for
Milestone 2 — nothing speculative beyond it.

The store just persists/reads bytes; the write-once immutability policy lives in
the ingestion CLI (it decides when to call put_text).
"""

from typing import Protocol

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import FilingDocument


class DocumentStore(Protocol):
    def exists(self, filing_id: int) -> bool: ...
    def get_text(self, filing_id: int) -> str | None: ...
    def put_text(self, filing_id: int, text: str, source_url: str | None) -> None: ...


class PostgresDocumentStore:
    """Stores cleaned filing text in the filing_documents table."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def exists(self, filing_id: int) -> bool:
        return (
            self._session.scalar(
                select(FilingDocument.id).where(
                    FilingDocument.filing_id == filing_id
                )
            )
            is not None
        )

    def get_text(self, filing_id: int) -> str | None:
        return self._session.scalar(
            select(FilingDocument.content_text).where(
                FilingDocument.filing_id == filing_id
            )
        )

    def put_text(self, filing_id: int, text: str, source_url: str | None) -> None:
        stmt = insert(FilingDocument).values(
            filing_id=filing_id,
            source_url=source_url,
            content_text=text,
            char_length=len(text),
        )
        # On --refresh the CLI re-derives; update text + length together.
        stmt = stmt.on_conflict_do_update(
            index_elements=["filing_id"],
            set_={
                "source_url": stmt.excluded.source_url,
                "content_text": stmt.excluded.content_text,
                "char_length": stmt.excluded.char_length,
            },
        )
        self._session.execute(stmt)
