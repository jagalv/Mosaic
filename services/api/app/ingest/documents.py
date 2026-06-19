"""Document ingestion CLI: fetch primary docs -> clean text + sections -> Postgres.

Builds on the filings already stored in Milestone 1 (does NOT re-ingest
financials). For each company it takes the most recent N 10-Ks and M 10-Qs,
fetches the primary document, stores cleaned text, and (for 10-Ks) segments it.

Usage (from services/api, venv active):
    python -m app.ingest.documents                  # all 10 default tickers
    python -m app.ingest.documents AAPL MSFT
    python -m app.ingest.documents --refresh AAPL   # re-derive text + re-segment
    python -m app.ingest.documents --limit-10k 3 --limit-10q 0 AAPL

Immutability: content_text is write-once. Without --refresh, a filing that
already has a stored document is skipped untouched. With --refresh we re-derive
the text AND re-segment in the same pass, so offsets and sections never drift.
"""

import sys
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.ingest import edgar
from app.ingest.run import DEFAULT_TICKERS
from app.ingest.sections import segment_filing
from app.ingest.storage import PostgresDocumentStore
from app.models import Company, Filing, FilingSection

DEFAULT_LIMIT_10K = 2
DEFAULT_LIMIT_10Q = 2


def _recent_filings(session: Session, cik: int, form: str, limit: int) -> list[Filing]:
    if limit <= 0:
        return []
    return list(
        session.scalars(
            select(Filing)
            .where(Filing.cik == cik, Filing.form_type == form)
            .order_by(Filing.filing_date.desc())
            .limit(limit)
        ).all()
    )


def _store_filing(
    session: Session, store: PostgresDocumentStore, filing: Filing, refresh: bool
) -> str:
    """Persist one filing's text + sections. Returns a short status string."""
    if not filing.primary_doc_url:
        return "no-url"
    if store.exists(filing.id) and not refresh:
        return "skip(exists)"  # immutable: leave text + sections untouched

    html = edgar.fetch_filing_document(
        filing.primary_doc_url, filing.accession_no, refresh=refresh
    )
    text, sections = segment_filing(html, filing.form_type)

    # Re-derive text and re-segment together so offsets stay consistent.
    store.put_text(filing.id, text, source_url=filing.primary_doc_url)
    session.execute(delete(FilingSection).where(FilingSection.filing_id == filing.id))
    for s in sections:
        session.add(
            FilingSection(
                filing_id=filing.id,
                section_code=s.section_code,
                title=s.title,
                order_index=s.order_index,
                char_start=s.char_start,
                char_end=s.char_end,
            )
        )
    return f"stored({len(text)} chars, {len(sections)} sections)"


def ingest_documents(
    session: Session,
    ticker: str,
    limit_10k: int,
    limit_10q: int,
    refresh: bool,
) -> None:
    company = session.scalar(select(Company).where(Company.ticker == ticker.upper()))
    if company is None:
        print(f"  {ticker:6s} SKIP — not in DB (run app.ingest.run first)")
        return

    store = PostgresDocumentStore(session)
    targets = _recent_filings(session, company.cik, "10-K", limit_10k) + _recent_filings(
        session, company.cik, "10-Q", limit_10q
    )
    for filing in targets:
        status = _store_filing(session, store, filing, refresh)
        session.commit()
        print(f"  {ticker:6s} {filing.form_type:5s} {filing.accession_no}  {status}")


def main(argv: list[str]) -> int:
    refresh = "--refresh" in argv
    limit_10k = _int_flag(argv, "--limit-10k", DEFAULT_LIMIT_10K)
    limit_10q = _int_flag(argv, "--limit-10q", DEFAULT_LIMIT_10Q)
    tickers = [a.upper() for a in argv if not a.startswith("--") and not a.isdigit()] or list(
        DEFAULT_TICKERS
    )

    print(
        f"Ingesting docs for {len(tickers)} ticker(s) at {datetime.now():%H:%M:%S} "
        f"(10-K={limit_10k}, 10-Q={limit_10q}, refresh={refresh})"
    )
    with SessionLocal() as session:
        for ticker in tickers:
            try:
                ingest_documents(session, ticker, limit_10k, limit_10q, refresh)
            except Exception as exc:
                session.rollback()
                print(f"  {ticker:6s} FAILED: {exc}")
    print("Done.")
    return 0


def _int_flag(argv: list[str], name: str, default: int) -> int:
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            return int(argv[i + 1])
    return default


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
