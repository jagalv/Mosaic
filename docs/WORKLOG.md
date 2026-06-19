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
**Prompted to:** Milestone 2 — store filing document text, segment 10-K sections, filing list + reader on the company page.
**Did:**
- Schema + migration `0003`: `filing_documents` (1:1 cleaned text) + `filing_sections` (code/title/order + char offsets). Hand-written; existing tables untouched.
- `app/ingest/sections.py` (HTML→text via bs4 + 10-K Item segmentation), `storage.py` (`DocumentStore` seam — Postgres impl now, R2 later), `documents.py` CLI (`python -m app.ingest.documents`). Caches raw HTML to `data/edgar/filings/`.
- Segmentation skips the TOC by requiring a non-empty same-line title (verified against real AAPL 10-K); `content_text` immutable except on `--refresh`, which re-segments in the same pass (stable offsets for M3 citations).
- API: `/company/{ticker}` now returns a `filings` list; new `/filing/{accession_no}` returns text + sections. Frontend: Filings card + `/filing/[accession]` reader with section nav.
- Golden test (`tests/test_filing_sections.py`) on a real AAPL FY2023 10-K text fixture: Item 1A Risk Factors present (~67.9k chars), Item 7 MD&A present, ordered/non-overlapping, TOC not mistaken for body; + html→text unit test.
**Verified:** Ingested docs for all 10 (latest 2×10-K + 2×10-Q each); 10-Ks → 22–23 sections, 10-Qs stored unsegmented. Idempotent re-run skips. `pytest` 9/9 green. `next build` clean. End-to-end: `/company/aapl` filings list → 10-K reader shows Risk Factors/MD&A via anchor nav.
**Next / handoff:** Milestone 3 (the wedge) — section-aware chunking + embeddings (pgvector) + hybrid retrieval + grounded cited answers, built on `filing_sections` char offsets. GOTCHAs: (1) XOM/JPM incorporate MD&A by reference → stub Item 7 in the primary doc (faithful, content lives in an exhibit we don't fetch). (2) 10-Q is unsegmented (Part-aware codes deferred). (3) Only latest 2 10-Ks/company ingested — the AAPL FY2023 fixture filing itself isn't in the DB. Did NOT commit — James to commit (messages in summary).
**Roadmap:** Milestone 2 — all 4 checkboxes ticked.

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

### 2026-06-18 — Bobby (Sonnet 4.6) [session 2]
**Prompted to:** Fix frontend not loading — `localhost:3000` showing `ERR_CONNECTION_REFUSED`.
**Did:**
- Diagnosed the issue: `npm run dev:web` had been Ctrl+C'd, so nothing was listening on port 3000. Docker and uvicorn were both fine.
- Walked James through rerunning `npm run dev:web` from the repo root and leaving the terminal running.
**Verified:** James confirmed with screenshot — Mosaic health page showing **API: ok / Database: ok** at 7:35 PM.
**Next / handoff:** Nothing broken. All three services running (Docker/Postgres, uvicorn/API, Next.js/frontend). Ready for Sally to hand Alexander the Milestone 1 prompt whenever James gives the go.
**Roadmap:** No changes — still at Milestone 0 complete, Milestone 1 not started.

---

### 2026-06-18 — Bobby (Sonnet 4.6)
**Prompted to:** Install Docker Desktop, run the Milestone 0 verify block, and push the repo to GitHub.
**Did:**
- Copied `.env.example` → `.env` and `apps/web/.env.local.example` → `apps/web/.env.local`.
- Guided James through Docker Desktop installation (AMD64), `docker compose up -d`, Python venv setup, `pip install`, `alembic upgrade head`, and `uvicorn` startup.
- Confirmed health check green: **API: ok / Database: ok** at localhost:3000.
- Committed (`feat: milestone 0 — skeleton health check (green)`, root commit `113a038`, 43 files).
- Created GitHub repo `jagalv/mosaic` and pushed — repo is now live.
**Verified:** James shared a screenshot of localhost:3000 showing both statuses green.
**Next / handoff:** Milestone 0 fully complete including GitHub push. ROADMAP "Push repo to GitHub" checkbox should be ticked. Ready for Milestone 1 — Sally to write the Alexander prompt when James gives the go.
**Roadmap:** Milestone 0 — GitHub push done (was the last open item).

---

### 2026-06-18 — Alexander (Claude Code)
**Prompted to:** Build Milestone 0 — a runnable skeleton (browser → FastAPI → Postgres → browser health check), local pipeline only.
**Did:**
- Scaffolded the monorepo (npm workspaces): `apps/web`, `services/api`, `services/ingest` stub, `packages/shared`.
- `services/api`: FastAPI app with `/health` that checks DB connectivity and degrades gracefully (`200` with `db: error`) when Postgres is down. SQLAlchemy + Alembic; migration `0001` enables pgvector and creates a `health_check` table.
- `apps/web`: Next.js (App Router) + Tailwind v4 + shadcn/ui; a status page that polls the API and shows "API: ok / Database: ok".
- Root tooling: `.gitignore`, `.env.example`, `docker-compose.yml` (local pgvector Postgres), `docs/DECISIONS.md` (5 entries), README "Running locally".
- Versions: Next 16.2.9 / React 19.2.4 / Tailwind v4; FastAPI 0.115.6 / SQLAlchemy 2.0.36 / Alembic 1.14.0 / psycopg 3.2.3.
**Verified:** `next build` clean (TS + lint); API boots; Alembic emits correct migration SQL; `/health` returns graceful `db: error` with no DB. **James later confirmed live `DB: ok` with Docker up.** Committed: `feat: milestone 0 — skeleton health check (green)`.
**Next / handoff:** Milestone 1 — SEC ingestion for ~10 companies (`companies`/`financials`/`filings` schema, EDGAR submissions + companyfacts XBRL, company page with multi-year financials, golden-fixture test). The hard part is messy XBRL → clean line items, not rendering.
**Roadmap:** Milestone 0 — local skeleton boxes ticked. Vercel deploy + auth **deferred** on purpose (not blockers). GitHub push still pending.

---

### 2026-06-18 — Sally (Opus 4.8)
**Prompted to:** Verify Milestone 0 and set up the multi-assistant coordination system.
**Did:**
- Verified the Milestone 0 build against the real files (matches the handoff). Removed a stray `MosaicTerm/` folder (stale duplicate README) and a leftover `.git/index.lock`.
- Created this WORKLOG, `CLAUDE.md` (auto-loaded by Alexander), and corrected the ROADMAP Milestone 0 checkboxes to reflect what's actually done vs. deferred.
**Verified:** Confirmed clean commit + empty working tree; ROADMAP now distinguishes done vs. deferred (Vercel, auth).
**Next / handoff:** James to decide whether to start Milestone 1. I'll write the Milestone 1 build prompt for Alexander when he gives the go.
**Roadmap:** No code milestones changed; tracker corrected for accuracy.
