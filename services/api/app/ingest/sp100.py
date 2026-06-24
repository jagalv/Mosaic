"""S&P 100 ticker universe for corpus expansion (M6a).

`SP100` is a static, committed snapshot of the S&P 100 (OEX) constituents, copied
from the Wikipedia "S&P 100" constituents table on 2026-06-24. It is intentionally
static — reproducible, offline, no runtime scraping. Index membership drifts over
time, so refresh it deliberately if needed; this is a convenience list, not a live
feed. The four ingestion CLIs accept tickers as args, so GROWING the corpus later
needs NO code change — pass more of `SP100` to `python -m app.ingest.batch`.

Resolution caveat: SEC `company_tickers.json` uses the dash form for dual-class
symbols (e.g. `BRK-B`, `BF-B`), while this list keeps Wikipedia's dot form
(`BRK.B`). Those few won't resolve via `resolve_cik` and will land in the batch
failure report — expected, not a bug. Don't pre-perfect; the report surfaces them.

`BATCH_20` is this slice's curated set: the original 10 starter tickers plus ~10
more widely recognized large caps spanning sectors. All are clean single-symbol
tickers that resolve directly against the SEC file.
"""

# The original 10 starter companies (mirrors app/ingest/run.DEFAULT_TICKERS).
_STARTERS = (
    "AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "JPM", "KO", "XOM", "UNH",
)

# ~10 more recognizable large caps across sectors for M6a (all clean symbols).
_M6A_ADDITIONS = (
    "JNJ",   # healthcare / pharma
    "PFE",   # healthcare / pharma
    "WMT",   # retail
    "PG",    # consumer staples
    "HD",    # retail / home improvement
    "DIS",   # media & entertainment
    "NFLX",  # media / streaming
    "V",     # financials / payments
    "BA",    # industrials / aerospace
    "CAT",   # industrials / machinery
)

BATCH_20: tuple[str, ...] = _STARTERS + _M6A_ADDITIONS

# Full S&P 100 (Wikipedia "S&P 100" constituents, 2026-06-24). Dual-class symbols
# kept in dot form; see the resolution caveat above.
SP100: tuple[str, ...] = (
    "AAPL", "ABBV", "ABT", "ACN", "ADBE", "AIG", "AMD", "AMGN", "AMT", "AMZN",
    "AVGO", "AXP", "BA", "BAC", "BK", "BKNG", "BLK", "BMY", "BRK.B", "C",
    "CAT", "CHTR", "CL", "CMCSA", "COF", "COP", "COST", "CRM", "CSCO", "CVS",
    "CVX", "DE", "DHR", "DIS", "DOW", "DUK", "EMR", "F", "FDX", "GD",
    "GE", "GILD", "GM", "GOOG", "GOOGL", "GS", "HD", "HON", "IBM", "INTC",
    "INTU", "ISRG", "JNJ", "JPM", "KHC", "KO", "LIN", "LLY", "LMT", "LOW",
    "MA", "MCD", "MDLZ", "MDT", "MET", "META", "MMM", "MO", "MRK", "MS",
    "MSFT", "NEE", "NFLX", "NKE", "NVDA", "ORCL", "PEP", "PFE", "PG", "PM",
    "PYPL", "QCOM", "RTX", "SBUX", "SCHW", "SO", "SPG", "T", "TGT", "TMO",
    "TMUS", "TSLA", "TXN", "UNH", "UNP", "UPS", "USB", "V", "VZ", "WFC",
    "WMT", "XOM",
)
