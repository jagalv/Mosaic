"""Golden test — pins the XBRL -> line-item mapping against a real filing.

The fixture (tests/fixtures/aapl_companyfacts.json) is a real subset of Apple's
SEC companyfacts (the mapped concepts, USD units). Values below were confirmed
against the actual data, not memory. A bad concept remap or a regression in the
fiscal-year-from-period-end / latest-filed logic will fail these.

Fully offline: no network, no database.
"""

import json
from pathlib import Path

from app.ingest.parse import parse_companyfacts

FIXTURE = Path(__file__).parent / "fixtures" / "aapl_companyfacts.json"


def _facts():
    return parse_companyfacts(json.loads(FIXTURE.read_text(encoding="utf-8")))


def _value(facts, line_item, fiscal_year):
    matches = [f.value for f in facts if f.line_item == line_item and f.fiscal_year == fiscal_year]
    assert len(matches) <= 1, f"{line_item} {fiscal_year} appeared {len(matches)} times"
    return matches[0] if matches else None


def test_aapl_fy2023_revenue():
    assert _value(_facts(), "Revenue", 2023) == 383_285_000_000


def test_aapl_fy2023_net_income():
    assert _value(_facts(), "NetIncome", 2023) == 96_995_000_000


def test_comparatives_assigned_by_period_end_not_filing_fy():
    # If fiscal_year were taken from the filing's `fy` field, prior-year
    # comparatives would collapse onto the filing year and FY2021 would be wrong
    # or missing. This is the milestone's #1 bug guard.
    assert _value(_facts(), "Revenue", 2021) == 365_817_000_000


def test_no_duplicate_line_item_per_fiscal_year():
    facts = _facts()
    keys = [(f.line_item, f.fiscal_year) for f in facts]
    assert len(keys) == len(set(keys)), "dedupe by (line_item, fiscal_year) failed"
