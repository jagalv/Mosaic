"""Read-only corpus QA survey (M6a).

Flags the messy/stub cases a wider, deeper corpus surfaces, so they're visible
at a glance. We ACCEPT partial data — incorporate-by-reference MD&A stubs (XOM,
JPM, ...), OLDER 10-Ks (3-4 yrs back) that segment poorly under older SEC HTML,
and companies missing some XBRL tags — this just makes them auditable; it does
not fix anything. Pure SELECTs: writes nothing.

Usage (from services/api, venv active; DATABASE_URL = the DB to inspect):
    python -m app.ingest.qa
"""

import sys

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db import SessionLocal

# A 10-K with fewer chunks than this very likely segmented poorly (or is a stub).
MIN_CHUNKS = 10
# A company with fewer distinct financial line items than this is missing tags.
MIN_LINE_ITEMS = 8


def corpus_summary(session: Session) -> dict:
    """Headline counts of the corpus as it currently stands in this DB."""
    def q(sql: str) -> int:
        return session.execute(text(sql)).scalar() or 0

    return {
        "companies": q("SELECT count(*) FROM companies"),
        "filings": q("SELECT count(*) FROM filings"),
        "filings_10k": q(
            "SELECT count(*) FROM filings WHERE form_type IN ('10-K','10-K/A')"
        ),
        "filing_documents": q("SELECT count(*) FROM filing_documents"),
        "filing_sections": q("SELECT count(*) FROM filing_sections"),
        "filing_chunks": q("SELECT count(*) FROM filing_chunks"),
        "chunks_embedded": q(
            "SELECT count(*) FROM filing_chunks WHERE embedding IS NOT NULL"
        ),
        "financial_facts": q("SELECT count(*) FROM financials"),
    }


# --- the three "messy data" flags ---

_ZERO_SECTION_10KS = """
    SELECT c.ticker, f.accession_no, f.filing_date
    FROM filings f
    JOIN companies c ON c.cik = f.cik
    JOIN filing_documents d ON d.filing_id = f.id
    LEFT JOIN (
        SELECT filing_id, count(*) AS n FROM filing_sections GROUP BY filing_id
    ) s ON s.filing_id = f.id
    WHERE f.form_type IN ('10-K','10-K/A') AND COALESCE(s.n, 0) = 0
    ORDER BY c.ticker, f.filing_date
"""

_LOW_CHUNK_10KS = """
    SELECT c.ticker, f.accession_no, f.filing_date, count(ch.id) AS n
    FROM filings f
    JOIN companies c ON c.cik = f.cik
    JOIN filing_documents d ON d.filing_id = f.id
    LEFT JOIN filing_chunks ch ON ch.filing_id = f.id
    WHERE f.form_type IN ('10-K','10-K/A')
    GROUP BY c.ticker, f.accession_no, f.filing_date
    HAVING count(ch.id) < :min_chunks
    ORDER BY n, c.ticker
"""

_LOW_FINANCIALS = """
    SELECT c.ticker, count(DISTINCT fin.line_item) AS n
    FROM companies c
    LEFT JOIN financials fin ON fin.cik = c.cik
    GROUP BY c.ticker
    HAVING count(DISTINCT fin.line_item) < :min_items
    ORDER BY n, c.ticker
"""


def survey(session: Session) -> None:
    summary = corpus_summary(session)
    print("== Corpus summary ==")
    for k, v in summary.items():
        print(f"  {k:18s} {v}")

    zero_sections = session.execute(text(_ZERO_SECTION_10KS)).all()
    print(f"\n== 10-Ks with 0 sections ({len(zero_sections)}) "
          "[stub MD&A / poor segmentation — accepted] ==")
    for r in zero_sections:
        print(f"  {r.ticker:6s} {r.accession_no}  filed {r.filing_date}")

    low_chunks = session.execute(
        text(_LOW_CHUNK_10KS), {"min_chunks": MIN_CHUNKS}
    ).all()
    print(f"\n== 10-Ks with < {MIN_CHUNKS} chunks ({len(low_chunks)}) "
          "[short/poorly-segmented — older filings expected here] ==")
    for r in low_chunks:
        print(f"  {r.ticker:6s} {r.accession_no}  filed {r.filing_date}  chunks={r.n}")

    low_fin = session.execute(
        text(_LOW_FINANCIALS), {"min_items": MIN_LINE_ITEMS}
    ).all()
    print(f"\n== Companies with < {MIN_LINE_ITEMS} financial line items "
          f"({len(low_fin)}) [missing XBRL tags — accepted] ==")
    for r in low_fin:
        print(f"  {r.ticker:6s} line_items={r.n}")


def main(argv: list[str]) -> int:
    with SessionLocal() as session:
        survey(session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
