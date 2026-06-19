"""Chunk ingestion CLI: stored filing text + sections -> filing_chunks.

Reads each filing's immutable content_text + FilingSection offsets (Milestone 2
output) and writes section-aware retrieval chunks. Embeddings are left NULL here
and filled by `python -m app.ingest.embed` (Slice B) so this step carries no
torch dependency.

Idempotent + embedding-preserving: chunks upsert on (filing_id, chunk_index).
Because content_text is immutable, a re-run reproduces identical chunks, every
content_hash matches, and existing embeddings are left untouched (we never
re-embed unchanged chunks). Only a chunk whose hash actually changed has its
embedding reset to NULL for re-embedding.

Usage (from services/api, venv active):
    python -m app.ingest.chunk                 # all default tickers' 10-Ks
    python -m app.ingest.chunk AAPL MSFT
"""

import sys
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.ingest.chunks import chunk_filing
from app.ingest.run import DEFAULT_TICKERS
from app.models import Company, Filing, FilingChunk, FilingDocument, FilingSection


def _chunk_one_filing(session: Session, filing: Filing) -> str:
    doc = session.scalar(
        select(FilingDocument).where(FilingDocument.filing_id == filing.id)
    )
    if doc is None:
        return "no-doc"

    sections = session.scalars(
        select(FilingSection)
        .where(FilingSection.filing_id == filing.id)
        .order_by(FilingSection.order_index)
    ).all()
    if not sections:
        return "no-sections"  # e.g. unsegmented 10-Q — out of M3 scope

    chunks = chunk_filing(
        doc.content_text,
        [(s.section_code, s.char_start, s.char_end) for s in sections],
    )
    if not chunks:
        return "no-chunks"

    rows = [
        {
            "filing_id": filing.id,
            "section_code": c.section_code,
            "chunk_index": c.chunk_index,
            "char_start": c.char_start,
            "char_end": c.char_end,
            "content_text": c.content_text,
            "content_hash": c.content_hash,
            "embedding": None,
        }
        for c in chunks
    ]
    stmt = insert(FilingChunk).values(rows)
    # Update only when the text actually changed; that resets embedding to NULL
    # so embed.py re-does it. Unchanged chunks are left exactly as-is.
    stmt = stmt.on_conflict_do_update(
        constraint="uq_chunks_filing_index",
        set_={
            "section_code": stmt.excluded.section_code,
            "char_start": stmt.excluded.char_start,
            "char_end": stmt.excluded.char_end,
            "content_text": stmt.excluded.content_text,
            "content_hash": stmt.excluded.content_hash,
            "embedding": None,
        },
        where=FilingChunk.content_hash != stmt.excluded.content_hash,
    )
    session.execute(stmt)
    # Drop any trailing chunks from a previous, longer run (e.g. after --refresh
    # shortened the text). Keeps the set exactly the current chunk count.
    session.execute(
        delete(FilingChunk).where(
            FilingChunk.filing_id == filing.id,
            FilingChunk.chunk_index >= len(chunks),
        )
    )
    return f"{len(chunks)} chunks"


def chunk_ticker(session: Session, ticker: str) -> None:
    company = session.scalar(select(Company).where(Company.ticker == ticker.upper()))
    if company is None:
        print(f"  {ticker:6s} SKIP — not in DB (run app.ingest.run first)")
        return

    filings = session.scalars(
        select(Filing)
        .where(Filing.cik == company.cik, Filing.form_type.in_(("10-K", "10-K/A")))
        .order_by(Filing.filing_date.desc())
    ).all()
    for filing in filings:
        status = _chunk_one_filing(session, filing)
        session.commit()
        print(f"  {ticker:6s} {filing.form_type:5s} {filing.accession_no}  {status}")


def main(argv: list[str]) -> int:
    tickers = [a.upper() for a in argv if not a.startswith("--")] or list(
        DEFAULT_TICKERS
    )
    print(f"Chunking 10-Ks for {len(tickers)} ticker(s) at {datetime.now():%H:%M:%S}")
    with SessionLocal() as session:
        for ticker in tickers:
            try:
                chunk_ticker(session, ticker)
            except Exception as exc:
                session.rollback()
                print(f"  {ticker:6s} FAILED: {exc}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
