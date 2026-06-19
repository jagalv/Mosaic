"""Embedding CLI: fill in vectors for chunks that don't have one yet.

Builds on chunks already written by `python -m app.ingest.chunk`. By default it
only embeds chunks whose `embedding IS NULL` — that is exactly the set of new or
content-changed chunks (chunk.py nulls the embedding when a chunk's text
changes), so we never re-embed unchanged text. `--all` forces a full re-embed.

Passages are embedded plain (the query-side prefix lives in embeddings.py).

Usage (from services/api, venv active):
    python -m app.ingest.embed              # embed all missing vectors
    python -m app.ingest.embed AAPL MSFT    # restrict to ticker(s)
    python -m app.ingest.embed --all        # re-embed everything (e.g. model swap)
"""

import sys
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.embeddings import embed_passages
from app.ingest.run import DEFAULT_TICKERS
from app.models import Company, Filing, FilingChunk

BATCH = 128


def _pending_query(force: bool, ciks: list[int] | None):
    q = select(FilingChunk.id, FilingChunk.content_text).order_by(FilingChunk.id)
    if not force:
        q = q.where(FilingChunk.embedding.is_(None))
    if ciks is not None:
        q = q.join(Filing, Filing.id == FilingChunk.filing_id).where(
            Filing.cik.in_(ciks)
        )
    return q


def embed_pending(session: Session, force: bool, ciks: list[int] | None) -> int:
    rows = session.execute(_pending_query(force, ciks)).all()
    if not rows:
        return 0

    done = 0
    for i in range(0, len(rows), BATCH):
        batch = rows[i : i + BATCH]
        vectors = embed_passages([text for _, text in batch])
        for (chunk_id, _), vec in zip(batch, vectors):
            session.execute(
                update(FilingChunk)
                .where(FilingChunk.id == chunk_id)
                .values(embedding=vec)
            )
        session.commit()
        done += len(batch)
        print(f"  embedded {done}/{len(rows)}")
    return done


def _resolve_ciks(session: Session, tickers: list[str]) -> list[int] | None:
    if not tickers:
        return None
    ciks: list[int] = []
    for t in tickers:
        company = session.scalar(select(Company).where(Company.ticker == t.upper()))
        if company is None:
            print(f"  {t:6s} SKIP — not in DB")
        else:
            ciks.append(company.cik)
    return ciks


def main(argv: list[str]) -> int:
    force = "--all" in argv
    tickers = [a.upper() for a in argv if not a.startswith("--")]
    print(
        f"Embedding chunks at {datetime.now():%H:%M:%S} "
        f"(force={force}, tickers={tickers or 'ALL'})"
    )
    with SessionLocal() as session:
        ciks = _resolve_ciks(session, tickers)
        n = embed_pending(session, force, ciks)
    print(f"Done. {n} chunk(s) embedded.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
