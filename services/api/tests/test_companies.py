"""Offline shape test for the public GET /companies browse endpoint (M6a).

No DB: a tiny fake session returns canned Company rows + canned Revenue facts, so
we pin the response shape the grid depends on — identity + latest/prior FY revenue
(one call, no per-company fan-out), in ticker order, with revenue_prev null when a
company has only one year.
"""

from decimal import Decimal

from fastapi.testclient import TestClient

from app.db import get_session
from app.main import app
from app.models import Company


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class _CompaniesDB:
    """scalars() -> the Company list; execute() -> the (cik, year, value) rows."""

    def __init__(self, companies, rev_rows):
        self._companies = companies
        self._rev = rev_rows

    def scalars(self, stmt):
        return _Result(self._companies)

    def execute(self, stmt):
        return _Result(self._rev)

    def close(self):
        pass


def test_companies_endpoint_shape():
    companies = [  # already in ticker order (the SQL ORDER BY is real in prod)
        Company(cik=320193, ticker="AAPL", name="Apple Inc.", sector="Manufacturing"),
        Company(cik=789019, ticker="MSFT", name="Microsoft Corp.", sector="Services"),
    ]
    rev_rows = [
        (320193, 2024, Decimal("391035000000")),
        (320193, 2023, Decimal("383285000000")),
        (789019, 2024, Decimal("245122000000")),  # MSFT: only one year
    ]
    db = _CompaniesDB(companies, rev_rows)

    def _override():
        yield db

    app.dependency_overrides[get_session] = _override
    try:
        body = TestClient(app).get("/companies").json()
    finally:
        app.dependency_overrides.clear()

    assert [c["ticker"] for c in body] == ["AAPL", "MSFT"]
    assert set(body[0]) == {"ticker", "name", "sector", "revenue", "revenue_prev"}
    assert body[0]["revenue"] == 391035000000 and body[0]["revenue_prev"] == 383285000000
    assert body[0]["sector"] == "Manufacturing"
    # One year of revenue -> current set, prior is null.
    assert body[1]["revenue"] == 245122000000 and body[1]["revenue_prev"] is None
