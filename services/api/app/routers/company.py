"""Company endpoint: serves the header + financials pivoted to a wide table.

The DB stores tall facts; we pivot to {statement -> [line_item -> {year: value}]}
here so the frontend can render year-columns directly. Line items follow the
concept-map order; only line items the company actually reports are included.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.ingest.concepts import LINE_ITEMS, STATEMENT_ORDER
from app.models import Company, Filing, FilingDocument, FilingSection, Financial

router = APIRouter()

MAX_YEARS = 5
MAX_FILINGS = 25


def _filings_list(db: Session, cik: int) -> list[dict]:
    """Recent filings with whether each has an ingested, segmented document."""
    filings = db.scalars(
        select(Filing)
        .where(Filing.cik == cik)
        .order_by(Filing.filing_date.desc())
        .limit(MAX_FILINGS)
    ).all()
    ids = [f.id for f in filings]
    if not ids:
        return []

    with_doc = set(
        db.scalars(
            select(FilingDocument.filing_id).where(FilingDocument.filing_id.in_(ids))
        ).all()
    )
    section_counts = dict(
        db.execute(
            select(FilingSection.filing_id, func.count())
            .where(FilingSection.filing_id.in_(ids))
            .group_by(FilingSection.filing_id)
        ).all()
    )
    return [
        {
            "accession_no": f.accession_no,
            "form_type": f.form_type,
            "filing_date": f.filing_date.isoformat() if f.filing_date else None,
            "period_of_report": (
                f.period_of_report.isoformat() if f.period_of_report else None
            ),
            "has_document": f.id in with_doc,
            "section_count": section_counts.get(f.id, 0),
        }
        for f in filings
    ]


def _json_number(value) -> float | int:
    f = float(value)
    return int(f) if f.is_integer() else f


@router.get("/companies")
def list_companies(db: Session = Depends(get_session)) -> list[dict]:
    """Public browse: every company plus a lightweight latest-revenue metric, in
    ONE call (the grid card shows name/ticker/sector + Revenue + YoY delta). Two
    queries total, no per-company fan-out."""
    companies = db.scalars(select(Company).order_by(Company.ticker)).all()

    # Latest two FY Revenue values per company → the card's value + delta.
    rev_rows = db.execute(
        select(Financial.cik, Financial.fiscal_year, Financial.value).where(
            Financial.line_item == "Revenue", Financial.fiscal_period == "FY"
        )
    ).all()
    by_cik: dict[int, list[tuple[int, object]]] = {}
    for cik, year, value in rev_rows:
        by_cik.setdefault(cik, []).append((year, value))

    out: list[dict] = []
    for c in companies:
        years = sorted(by_cik.get(c.cik, []), key=lambda yv: yv[0], reverse=True)
        out.append(
            {
                "ticker": c.ticker,
                "name": c.name,
                "sector": c.sector,
                "revenue": _json_number(years[0][1]) if years else None,
                "revenue_prev": _json_number(years[1][1]) if len(years) >= 2 else None,
            }
        )
    return out


@router.get("/company/{ticker}")
def get_company(ticker: str, db: Session = Depends(get_session)) -> dict:
    company = db.scalar(select(Company).where(Company.ticker == ticker.upper()))
    if company is None:
        raise HTTPException(status_code=404, detail=f"Company {ticker.upper()} not found")

    rows = db.scalars(
        select(Financial).where(
            Financial.cik == company.cik, Financial.fiscal_period == "FY"
        )
    ).all()

    years = sorted({r.fiscal_year for r in rows}, reverse=True)[:MAX_YEARS]
    year_set = set(years)

    # (line_item, year) -> value, for the selected years only.
    lookup: dict[tuple[str, int], object] = {
        (r.line_item, r.fiscal_year): r.value
        for r in rows
        if r.fiscal_year in year_set
    }

    statements: dict[str, list] = {s: [] for s in STATEMENT_ORDER}
    for spec in LINE_ITEMS:
        values = {
            str(y): _json_number(lookup[(spec.line_item, y)])
            for y in years
            if (spec.line_item, y) in lookup
        }
        if not values:
            continue  # company doesn't report this line item — omit the row
        statements[spec.statement_type].append(
            {"line_item": spec.line_item, "values": values}
        )

    return {
        "ticker": company.ticker,
        "name": company.name,
        "sector": company.sector,
        "industry": company.industry,
        "years": years,
        "statements": statements,
        "filings": _filings_list(db, company.cik),
    }
