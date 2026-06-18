"""companyfacts JSON -> clean annual financial facts.

This is the milestone's hard part. The key correctness rule:

  fiscal_year is derived from each fact's PERIOD END date, never from the
  `fy`/`fp` fields. Those describe the *reporting filing's* period, so a 10-K's
  comparative prior-year rows carry the filing's fy (e.g. all of FY2023/22/21
  revenue tagged fy=2023). Trusting them mislabels comparatives.

Per (line_item, fiscal_year) we keep the LATEST-FILED value (dedupe on each
fact's own `filed` date), which prefers restated over as-originally-reported.
"""

from dataclasses import dataclass
from datetime import date, datetime

from app.ingest.concepts import LINE_ITEMS, LineItemSpec

ANNUAL_FORMS = {"10-K", "10-K/A"}
# Full-year duration window. Covers 52/53-week fiscal years (e.g. Apple ~371d)
# while excluding quarterly (~90d) and 6/9-month YTD facts that share the tag.
_MIN_YEAR_DAYS = 350
_MAX_YEAR_DAYS = 380


@dataclass(frozen=True)
class ParsedFact:
    statement_type: str
    line_item: str
    concept: str
    fiscal_year: int
    fiscal_period: str  # 'FY'
    value: float
    unit: str  # 'USD'
    source_accession: str | None
    filed_date: date | None


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def _winning_concept(facts_us_gaap: dict, spec: LineItemSpec) -> tuple[str, list] | None:
    """First concept in the fallback list that has USD entries."""
    for concept in spec.concepts:
        node = facts_us_gaap.get(concept)
        if not node:
            continue
        usd = node.get("units", {}).get("USD")
        if usd:
            return concept, usd
    return None


def _eligible_entries(usd_entries: list, spec: LineItemSpec):
    """Yield (fiscal_year, entry) for annual entries matching the spec's kind."""
    for entry in usd_entries:
        if entry.get("form") not in ANNUAL_FORMS:
            continue
        end = _parse_date(entry.get("end"))
        if end is None:
            continue

        if spec.kind == "duration":
            start = _parse_date(entry.get("start"))
            if start is None:
                continue  # instant fact under a duration concept; skip
            span = (end - start).days
            if not (_MIN_YEAR_DAYS <= span <= _MAX_YEAR_DAYS):
                continue  # quarterly / YTD-partial
        # instant: no span check; the entry sits at the period end.

        yield end.year, entry


def parse_companyfacts(companyfacts: dict) -> list[ParsedFact]:
    """Extract one ParsedFact per (line_item, fiscal_year) we can map."""
    us_gaap = companyfacts.get("facts", {}).get("us-gaap", {})
    results: list[ParsedFact] = []

    for spec in LINE_ITEMS:
        found = _winning_concept(us_gaap, spec)
        if found is None:
            continue  # company doesn't report this line item — leave it absent
        concept, usd_entries = found

        # Pick the latest-filed entry for each fiscal year.
        best: dict[int, dict] = {}
        for fy, entry in _eligible_entries(usd_entries, spec):
            current = best.get(fy)
            if current is None or _is_later_filed(entry, current):
                best[fy] = entry

        for fy, entry in best.items():
            results.append(
                ParsedFact(
                    statement_type=spec.statement_type,
                    line_item=spec.line_item,
                    concept=concept,
                    fiscal_year=fy,
                    fiscal_period="FY",
                    value=entry["val"],
                    unit="USD",
                    source_accession=entry.get("accn"),
                    filed_date=_parse_date(entry.get("filed")),
                )
            )

    return results


def _is_later_filed(candidate: dict, current: dict) -> bool:
    """True if `candidate` was filed after `current` (ties -> keep current)."""
    c_filed = candidate.get("filed") or ""
    cur_filed = current.get("filed") or ""
    return c_filed > cur_filed  # ISO 'YYYY-MM-DD' sorts lexicographically
