# Decisions

A short, dated log of real architectural choices. Newest first. One entry per
genuine decision — not a changelog.

---

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
JS via root npm workspaces; e