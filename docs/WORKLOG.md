# Mosaic — Work Log

Shared memory across AI assistants (Sally, Bobby, Alexander). The three of us don't
share memory — this file is how we hand off. **Newest entry at the top.**

## Rules for every assistant
- **Read the latest entry at the start of your session.**
- **Append a new entry at the end of your session — always, without being asked.** A
  task isn't done until it's logged here.
- Keep entries concise and structured (use the template). This is a captain's log, NOT
  a transcript — do not paste full prompts or full responses. Summarize.
- Sign every entry with your name + model + date.

## Entry template (copy this, fill it in, put it at the TOP under the divider)
```
### YYYY-MM-DD — <Name> (<model>)
**Prompted to:** <one line: what James asked you to do>
**Did:** <what actually changed — files, features, fixes. A few bullets max.>
**Verified:** <how you checked it works, or "not verified — why">
**Next / handoff:** <what the next assistant should pick up, and any gotchas>
**Roadmap:** <milestone + which checkboxes you ticked, if any>
```

---

### 2026-06-18 — Alexander (Claude Code)
**Prompted to:** Milestone 1 — SEC ingestion + company page for 10 tickers (AAPL MSFT NVDA GOOGL AMZN META JPM KO XOM UNH). No AI, no auth.
**Did:**
- Schema + migration `0002`: `companies`, `filings`, `financials` (tall facts; `filed_date` added for audit). Hand-fixed autogenerate that wanted to drop `health_check`.
- Ingestion CLI in `services/api/app/ingest/` (`edgar.py` cache+throttle+UA-from-env, `concepts.py` map, `parse.py`, `run.py`). Caches raw EDGAR JSON to `data/edgar/` (gitignored); idempotent upserts on natural keys.
- XBRL parse rule: `fiscal_year` from period **end date** (not `fy`/`fp`); dedupe per (line_item, year) keeping latest-`filed`. Annual (10-K) only, USD only, full-year duration filter.
- API `GET /company/{ticker}` pivots tall → year-columns; Next.js `/company/[ticker]` server component renders 3 statement tables (5 yrs).
- Golden test (`tests/test_golden_financials.py`) on a real AAPL fixture: FY2023 Revenue 383,285M & NetIncome 96,995M, FY2021 365,817M (comparatives guard), no dupes.
**Verified:** Ingested all 10 (e.g. AAPL 264 financials). `pytest` 4/4 green. `next build` clean. End-to-end: `/company/aapl` HTML shows Apple Inc. + 383,285 / 96,995; unknown ticker → 404. JPM correctly lacks Current Assets/Liabilities (bank, unclassified) — expected.
**Next / handoff:** Milestone 2 — store raw 10-K/10-Q text → R2, `filing_sections` table + section segmentation, filing list + reader on the company page. Note: company page reads live API (`NEXT_PUBLIC_API_URL`); API must be running. `data/` is cached so re-ingest is offline unless `--refresh`. Did NOT commit — James to commit (suggested messages in session summary).
**Roadmap:** Milestone 1 — all 6 checkboxes ticked.

---

### 2026-06-18 — Bobby (Sonnet 4.6)
**Prompted to:** Install Docker Desktop, run the Milestone 0 verify block, and push the repo to GitHub.
**Did:**
- Copied `.env.example` → `.env` and `apps/web/.env.local.example` → `apps/web/.env.local`.
- Guided James through Docker Desktop installation (AMD64), `docker compose up -d`, Python venv setup, `pip install`, `alembic upgrade head`, and `uvicorn` startup.
- Confirmed health check green: **API: ok / Database: ok** at localhost:3000.
- Committed (`feat: milestone 0 — skeleton health check (green)`, root commit `113a038`, 43 files).
- Created GitHub repo `jagalv/mosaic` and pushed — repo is now live.
**Ve