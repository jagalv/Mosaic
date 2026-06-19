# Decisions

A short, dated log of real architectural choices. Newest first. One entry per
genuine decision — not a changelog.

---

## 2026-06-18 — Defer Cloudflare R2; store filing text in Postgres behind a seam

**Decision:** Milestone 2 stores cleaned filing text in Postgres
(`filing_documents.content_text`), not R2. Body-text persistence sits behind a
small `DocumentStore` seam (`PostgresDocumentStore` today) so an `R2DocumentStore`
can drop in later without touching ingestion, the segmenter, or the API.

**Why:** R2 needs an external account + a managed secret and adds setup friction
for a $0 solo project; at ~10 companies × a few filings (tens of MB) Postgres is
trivially sufficient. The seam keeps R2 a clean future swap (likely Phase 2 when
the corpus grows). Raw HTML is cached to gitignored `data/edgar/filings/` so
re-segmentation is offline. Decided by James on approval.

## 2026-06-18 — Section segmentation: TOC-skip by same-line title; content_text immutable

**Decision:** Segment 10-K Item sections from cleaned text by line-anchored
"Item N" headings, requiring a **non-empty same-line title** to skip the table
of contents (TOC entries wrap their title to the next line), plus last-occurrence
per code as a backstop. `content_text` is **immutable once stored**; it is only
re-derived on `--refresh`, which re-segments in the same pass so char offsets and
sections never drift.

**Why:** Confirmed against the real AAPL 10-K — the TOC lists every Item with the
title on a separate line, while body headings carry the title inline; the
same-line-title rule cleanly separates them. Offsets must be stable because
Milestone 3 citations will deep-link into `content_text` by character range.
Honest limitation: filers that **incorporate a section by reference** to a
separate exhibit (e.g. XOM/JPM MD&A → "Financial Section") yield a stub in the
primary document — faithful, but the content isn't there. We fetch the primary
document only; exhibit-chasing is out of scope.

## 2026-06-18 — 10-K segmented now; 10-Q text stored, sectioning deferred

**Decision:** Fully segment 10-K filings; store 10-Q document text but do not
segment it this milestone (reader shows full text).

**Why:** 10-Q repeats Item numbers across Part I and Part II (two "Item 1"s), so
robust sectioning needs Part-aware codes — extra work with no Milestone 2 payoff.
10-K is the high-value target Milestone 3 RAG builds on. Decided by James on
approval.

## 2026-06-18 — Ingestion lives in services/api (services/ingest stays a stub)

**Decision:** Milestone 1 SEC ingestion is a CLI inside `services/api`
(`app/ingest/`, run via `python -m app.ingest.run`), not the separate
`services/ingest` service.

**Why:** One Python env, one set of models, one deploy unit while ingestion is a
manual, low-volume CLI. Splitting it out now would duplicate config/models/DB
wiring for no benefit. Revisit when ingestion becomes a scheduled/long-running
job (its own resource profile) — then `services/ingest` graduates from stub.

## 2026-06-18 — fiscal_year derived from period END date, not XBRL fy/fp

**Decision:** In the companyfacts parser, a fact's fiscal year comes from its
period `end` date; the `fy`/`fp` fields are ignored for year assignment.

**Why:** `fy`/`fp` describe the *reporting filing's* period, so a 10-K's
comparative prior-year rows all carry the filing's fy (e.g. FY2023/22/21 revenue
all tagged fy=2023). Trusting them mislabels comparatives. Duplicates per
(line_item, year) are then deduped keeping the latest-`filed` value. The golden
test pins exactly this (AAPL FY2023 = 383,285M, and FY2021 distinct = 365,817M).

## 2026-06-18 — Tall financials + pivot in the API (no SQL view yet)

**Decision:** Store financials tall (one row per line-item/year); the
`/company/{ticker}` endpoint pivots to year-columns in Python. No DB view.

**Why:** Tall storage is flexible (new line items = new rows, not schema
changes) and the unique key makes ingestion idempotent. At one-company-per-
request scale a Python pivot is trivial and clearer than a materialized view;
add a view only if a cross-company query later needs it.

---

## 2026-06-18 — JS package manager: npm workspaces

**Decision:** Use npm workspaces (`apps/*`, `packages/*`) rather than pnpm/yarn.

**Why:** npm 11 ships on the dev machine; pnpm was not installed. Workspaces
cover the monorepo's needs (one frontend + a shared package) with zero extra
global tooling. Revisit if install times or strict dep isolation become a pain —
pnpm is the obvious upgrade and the switch is low-cost at this size.

## 2026-06-18 — Monorepo layout: separate JS and Python toolchains

**Decision:** One repo, but the JS and Python sides are managed independently.
JS via root npm workspaces; each Python service (`services/api`, later
`services/ingest`) gets its own `.venv` + pinned `requirements.txt`. No tool
tries to manage both languages.

**Why:** Avoids forcing a polyglot meta-tool (Nx/Turborepo/Bazel) we don't need
yet. Each side uses its native, boring tooling. The shared contract between them
is HTTP + env vars, not a build graph.

## 2026-06-18 — Migrations: Alembic, URL from app settings

**Decision:** Alembic for schema migrations. The DB URL is injected into
`alembic/env.py` from `app.config` (which reads `DATABASE_URL`), not stored in
`alembic.ini`.

**Why:** Alembic is the standard companion to SQLAlchemy and supports
autogenerate once we add models. Sourcing the URL from one place means the app
and migrations can never disagree on the target DB, and no connection string is
ever committed.

## 2026-06-18 — Local DB: docker-compose with the pgvector image

**Decision:** Local Postgres runs via `docker compose up` using
`pgvector/pgvector:pg16`. The app connects through `DATABASE_URL`.

**Why:** The official pgvector image has the extension preinstalled, so local
dev matches the prod feature set (we'll need vectors in Milestone 3). Because
the app only knows a `DATABASE_URL`, pointing at a hosted Postgres
(Supabase/Neon) later is a one-line env change — no code edits.

## 2026-06-18 — DB driver: psycopg 3 (binary)

**Decision:** `psycopg[binary]` (v3) with the `postgresql+psycopg://` SQLAlchemy
URL scheme.

**Why:** psycopg 3 is the current maintained driver; the binary build needs no
local libpq or compiler, which matters on the Windows dev machine. Swap to a
source build in production images if/when we want to avoid the binary wheel.
