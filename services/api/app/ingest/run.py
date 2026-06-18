"""Ingestion CLI: ticker(s) -> EDGAR -> Postgres.

Usage (from services/api, venv active):
    python -m app.ingest.run                 # all 10 default tickers
    python -m app.ingest.run AAPL MSFT       # a subset
    python -m app.ingest.run --refresh AAPL  # bypass the on-disk cache

Idempotent: upserts on natural keys, safe to rerun.
"""

import sys
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert

from app.db import SessionLocal
from app.ingest import edgar
from app.ingest.parse import parse_companyfacts
from app.models import Company, Filing, Financial

DEFAULT_TICKERS = (
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "KO", "XOM", "UNH",
)

# Forms we store in `filings` (facts ingestion is 10-K only; we list 10-Q too
# so the page can later show the filing history).
FILING_FORMS = {"10-K", "10-K/A", "10-Q", "10-Q/A"}


def sic_to_sector(sic: str | None) -> str | None:
    """Coarse SIC-range -> sector label. Approximate (SEC gives SIC, not GICS)."""
    if not sic or not sic.isdigit():
        return None
    code = int(sic)
    ranges = [
        (100, 999, "Agriculture"),
        (1000, 1499, "Mining"),
        (1500, 1799, "Construction"),
        (2000, 3999, "Manufacturing"),
        (4000, 4999, "Transportation & Utilities"),
        (5000, 5199, "Wholesale Trade"),
        (5200, 5999, "Retail Trade"),
        (6000, 6799, "Finance & Insurance"),
        (7000, 8999, "Services"),
        (9100, 9999, "Public Administration"),
    ]
    for lo, hi, label in ranges:
        if lo <= code <= hi:
            return label
    return None


def _primary_doc_url(cik: int, accession_no: str, primary_doc: str) -> str | None:
    if not primary_doc:
        return None
    nodash = accession_no.replace("-", "")
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{nodash}/{primary_doc}"


def _upsert_company(session, cik: int, ticker: str, submissions: dict) -> None:
    stmt = insert(Company).values(
        cik=cik,
        ticker=ticker.upper(),
        name=submissions.get("name", ticker.upper()),
        sector=sic_to_sector(submissions.get("sic")),
        industry=submissions.get("sicDescription"),
        updated_at=func.now(),
    )
    stmt = stmt.on_conflict_do_update(
        index_elements=["cik"],
        set_={
            "ticker": stmt.excluded.ticker,
            "name": stmt.excluded.name,
            "sector": stmt.excluded.sector,
            "industry": stmt.excluded.industry,
            "updated_at": func.now(),
        },
    )
    session.execute(stmt)


def _upsert_filings(session, cik: int, submissions: dict) -> int:
    recent = submissions.get("filings", {}).get("recent", {})
    forms = recent.get("form", [])
    accns = recent.get("accessionNumber", [])
    fdates = recent.get("filingDate", [])
    rdates = recent.get("reportDate", [])
    docs = recent.get("primaryDocument", [])

    count = 0
    for i, form in enumerate(forms):
        if form not in FILING_FORMS:
            continue
        accession_no = accns[i]
        stmt = insert(Filing).values(
            cik=cik,
            accession_no=accession_no,
            form_type=form,
            filing_date=fdates[i] or None,
            period_of_report=(rdates[i] or None) if i < len(rdates) else None,
            primary_doc_url=_primary_doc_url(
                cik, accession_no, docs[i] if i < len(docs) else ""
            ),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["accession_no"],
            set_={
                "cik": stmt.excluded.cik,
                "form_type": stmt.excluded.form_type,
                "filing_date": stmt.excluded.filing_date,
                "period_of_report": stmt.excluded.period_of_report,
                "primary_doc_url": stmt.excluded.primary_doc_url,
            },
        )
        session.execute(stmt)
        count += 1
    return count


def _upsert_financials(session, cik: int, companyfacts: dict) -> int:
    facts = parse_companyfacts(companyfacts)
    for f in facts:
        stmt = insert(Financial).values(
            cik=cik,
            fiscal_year=f.fiscal_year,
            fiscal_period=f.fiscal_period,
            statement_type=f.statement_type,
            concept=f.concept,
            line_item=f.line_item,
            value=f.value,
            unit=f.unit,
            source_accession=f.source_accession,
            filed_date=f.filed_date,
        )
        stmt = stmt.on_conflict_do_update(
            constraint="uq_financials_cik_line_year_period",
            set_={
                "statement_type": stmt.excluded.statement_type,
                "concept": stmt.excluded.concept,
                "value": stmt.excluded.value,
                "unit": stmt.excluded.unit,
                "source_accession": stmt.excluded.source_accession,
                "filed_date": stmt.excluded.filed_date,
            },
        )
        session.execute(stmt)
    return len(facts)


def ingest_ticker(session, ticker: str, tickers_data: dict, refresh: bool) -> None:
    cik = edgar.resolve_cik(ticker, tickers_data)
    submissions = edgar.fetch_submissions(cik, refresh=refresh)
    companyfacts = edgar.fetch_companyfacts(cik, refresh=refresh)

    _upsert_company(session, cik, ticker, submissions)
    n_filings = _upsert_filings(session, cik, submissions)
    n_facts = _upsert_financials(session, cik, companyfacts)
    session.commit()
    print(f"  {ticker:6s} CIK {cik:<10d} filings={n_filings:<4d} financials={n_facts}")


def main(argv: list[str]) -> int:
    refresh = "--refresh" in argv
    tickers = [a.upper() for a in argv if not a.startswith("--")] or list(DEFAULT_TICKERS)

    print(f"Ingesting {len(tickers)} ticker(s) at {datetime.now():%H:%M:%S} "
          f"(refresh={refresh})")
    tickers_data = edgar.fetch_company_tickers(refresh=refresh)

    with SessionLocal() as session:
        for ticker in tickers:
            try:
                ingest_ticker(session, ticker, tickers_data, refresh)
            except Exception as exc:
                session.rollback()
                print(f"  {ticker:6s} FAILED: {exc}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
