"""Company endpoint: serves the header + financials pivoted to a wide table.

The DB stores tall facts; we pivot to {statement -> [line_item -> {year: value}]}
here so the frontend can render year-columns directly. Line items follow the
concept-map order; only line items the company actually reports are included.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.ingest.concepts import LINE_ITEMS, STATEMENT_ORDER
from app.models import Company, Financial

router = APIRouter()

MAX_YEARS = 5


def _json_number(value) -> float | int:
    f = float(value)
    return int(f) if f.is_integer() else f


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
    }
