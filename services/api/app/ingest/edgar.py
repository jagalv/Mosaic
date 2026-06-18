"""SEC EDGAR HTTP client with on-disk caching and throttling.

All free/official EDGAR endpoints. Responses are cached to data/edgar/
(gitignored) so reruns don't re-hit SEC. Pass refresh=True to force a re-fetch.

SEC requires a real contact in the User-Agent and asks for <=10 req/s. We send
SEC_USER_AGENT on every request and keep a minimum gap between live calls; the
total volume here is tiny (~1 + 2 per company) but we stay polite regardless.
"""

import json
import time
from pathlib import Path

import httpx

from app.config import REPO_ROOT, get_settings

CACHE_DIR = REPO_ROOT / "data" / "edgar"

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik10}.json"
COMPANYFACTS_URL = "https://data.sec.gov/api/xbrl/companyfacts/CIK{cik10}.json"

_MIN_INTERVAL_S = 0.15  # ~6.7 req/s ceiling, comfortably under SEC's 10 req/s
_last_request_at = 0.0


def cik10(cik: int | str) -> str:
    """Zero-pad a CIK to the 10-digit form EDGAR URLs expect."""
    return str(int(cik)).zfill(10)


def _user_agent() -> str:
    ua = get_settings().sec_user_agent.strip()
    if not ua or "you@example.com" in ua:
        raise RuntimeError(
            "SEC_USER_AGENT is unset or still the placeholder. Set a real contact "
            'in .env, e.g. SEC_USER_AGENT="Mosaic research your-name@email.com". '
            "SEC blocks requests without a valid contact."
        )
    return ua


def _throttle() -> None:
    global _last_request_at
    gap = time.monotonic() - _last_request_at
    if gap < _MIN_INTERVAL_S:
        time.sleep(_MIN_INTERVAL_S - gap)
    _last_request_at = time.monotonic()


def _get_json(url: str, cache_name: str, refresh: bool = False) -> dict:
    """Return parsed JSON from cache, or fetch + cache it."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / cache_name

    if cache_path.exists() and not refresh:
        return json.loads(cache_path.read_text(encoding="utf-8"))

    _throttle()
    resp = httpx.get(url, headers={"User-Agent": _user_agent()}, timeout=30.0)
    resp.raise_for_status()
    cache_path.write_text(resp.text, encoding="utf-8")
    return resp.json()


def fetch_company_tickers(refresh: bool = False) -> dict:
    return _get_json(COMPANY_TICKERS_URL, "company_tickers.json", refresh)


def fetch_submissions(cik: int | str, refresh: bool = False) -> dict:
    padded = cik10(cik)
    return _get_json(
        SUBMISSIONS_URL.format(cik10=padded), f"submissions_CIK{padded}.json", refresh
    )


def fetch_companyfacts(cik: int | str, refresh: bool = False) -> dict:
    padded = cik10(cik)
    return _get_json(
        COMPANYFACTS_URL.format(cik10=padded),
        f"companyfacts_CIK{padded}.json",
        refresh,
    )


def resolve_cik(ticker: str, tickers_data: dict) -> int:
    """Map a ticker symbol to its integer CIK using company_tickers.json.

    That file is a dict keyed by row index: {"0": {"cik_str", "ticker", "title"}, ...}
    """
    want = ticker.strip().upper()
    for row in tickers_data.values():
        if row.get("ticker", "").upper() == want:
            return int(row["cik_str"])
    raise KeyError(f"Ticker {ticker!r} not found in company_tickers.json")
