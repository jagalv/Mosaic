# Decisions

A short, dated log of real architectural choices. Newest first. One entry per
genuine decision — not a changelog.

---

## 2026-06-19 — M4 auth/RLS stack: local-first, DB-enforced Postgres RLS (no auth SaaS)

**Decision (Sally, on James's delegation):** Milestone 4 auth + row-level security is built
**local-first** on the existing Docker Postgres — no Supabase / Clerk / managed auth.
- **Auth:** email + password. Passwords hashed with **argon2** (`argon2-cffi`; bcrypt via
  `passlib` is an acceptable fallback if install snags). Session = a signed **JWT in an httpOnly,
  Secure, SameSite=Lax cookie** (never localStorage). A `get_current_user` FastAPI dependency reads
  + verifies the cookie. JWT signing secret comes from an env var (e.g. `AUTH_SECRET_KEY`) — in
  `.env.example` as a placeholder, never hardcoded.
- **RLS = real Postgres row-level security.** User-owned tables (`watchlists`, `watchlist_items`,
  `notes`) get `ENABLE ROW LEVEL SECURITY` + policies keyed on
  `current_setting('app.current_user_id')`. Each authenticated request opens a transaction and runs
  `SET LOCAL app.current_user_id = <uid>` before any query, so isolation is enforced by the DB, not
  app code. A **cross-user security test** proves user A can never read/write user B's rows — through
  the DB and through the API.

**Why:** Project goal is personal-use + recruiter-cloneable at ~$0 (see 2026-06-18 objective).
Local RLS keeps the $0 / clone-and-run constraints (a recruiter runs `docker compose` + migrations,
no third-party signup) AND is the most senior-grade, correct reading of "a user only ever sees their
own data" — DB-enforced isolation with a real security test beats app-level checks. No new infra;
building auth from scratch is itself a portfolio signal.

**The gotcha to guard:** `SET LOCAL` must run inside the request's transaction (not globally on a
pooled connection) or the user id leaks across pooled connections. The cross-user test must cover it.
Two more for the cookie path: (1) `Secure` must be conditional on env so login works over
`http://localhost` in dev; (2) cross-port cookies (3000→8000) need `credentials: "include"` +
`allow_credentials=True` with a specific CORS origin (not `*`).

**Amendment (2026-06-19, during M4b) — a dedicated non-superuser app role is REQUIRED.** The
locked "single local role + `FORCE ROW LEVEL SECURITY`" turned out to be insufficient: the docker
`mosaic` role is the bootstrap **superuser**, and a superuser (or any `BYPASSRLS` role) bypasses RLS
*unconditionally* — `FORCE` only binds the table *owner*, never a superuser. M4b's security test
correctly caught this (user A saw user B's rows). Resolution (Sally's call, still Option-A / $0 /
clone-safe): a non-superuser role **`mosaic_app`** (`NOSUPERUSER NOBYPASSRLS`) created by a migration,
granted CRUD on app tables + sequences (RLS does the per-row filtering — coarse grants + forced
policies, the same model Supabase uses). **The API request path connects as `mosaic_app`
(`APP_DATABASE_URL`); migrations + ingestion + eval keep the admin `mosaic` role (`DATABASE_URL`)** —
admin is still needed for `CREATE EXTENSION vector` and bulk ingest. No silent fallback to the
superuser URL (that would re-open the hole). Also: implementation uses `set_config('app.current_user_id',
:uid, true)` rather than `SET LOCAL` (transaction-scoped AND parameter-safe — `SET LOCAL` can't bind).

## 2026-06-19 — Design system: Linear/Vercel modern fintech, teal accent, dark-first

**Decision:** A token-driven design system in `apps/web/app/globals.css` (extending
the existing oklch shadcn tokens, not replacing them), so every screen inherits
the look rather than being styled one-off. Locked direction: confident cool-neutral
base (hue 248) with ONE teal accent, **dark-mode-first**, hairline borders over
shadows, tabular numerals on all financial figures.

**Key choices:**
- **Accent = teal**, brand/interactive only: `--primary` dark `oklch(0.72 0.12 190)`,
  light `oklch(0.58 0.13 195)`. Semantic colors stay distinct hues so trust signals
  never read as accent: success/green `~152`, warning/amber `~75–85`, danger/red
  `~25–27`.
- **Layered surfaces** (page < panel < card): dark bg `0.165` / sidebar `0.185` /
  card `0.205`; light bg `0.985` / sidebar `0.975` / card `1`. Hairline border dark
  `oklch(1 0 0 / 9%)`, light `oklch(0.915 0.004 248)`. `--radius` `0.625rem`.
- **Active-citation highlight = violet** (`--highlight` dark `oklch(0.5 0.13 295)`,
  light `oklch(0.9 0.06 300)`), deliberately distinct from teal accent and the amber
  numbers-guard banner, and legible in both modes (James's guardrail).
- **Theme:** inline blocking script in the root layout sets `.dark` before first
  paint (default DARK, does NOT follow OS preference, no flash), persisted to
  `localStorage`; no `next-themes` dependency.
- **App shell** via an `(app)` route group (sidebar + top bar, custom/lean, mobile
  drawer) — URLs unchanged; old flat routes removed. Hero `/` stays full-bleed.
- **Type:** fixed the self-referential `--font-sans` bug (Geist Sans now actually
  applies); Geist Mono + `font-variant-numeric: tabular-nums` via a `.tnum` utility
  on every figure; tight heading tracking.
- **New deps: only `skeleton` + `tooltip`** (both free; no paid fonts/UI/animation
  libs). Fonts stay self-hosted Geist via next/font.

**Why:** Polish is ~as important as features for James's portfolio/demo goal. A
system (tokens + a few reusable primitives) means next session's M4 auth/workspace
screens are born consistent. Token values are a starting point to fine-tune from
light+dark review; `globals.css` is the source of truth.

## 2026-06-19 — Runtime numbers guard: digit-core match, ≥4 digits, flag-and-warn

**Decision:** Every significant figure an answer emits is checked in code against
the retrieved text (`app/rag/guard.py`), not just trusted to the prompt. Matching
is by **digit-core** (strip `$`, commas, `%`, decimals, scale words → compare digit
substrings), so `$383,285 million` / `383,285` / `383285000000` all match a source
`383,285`. Only **≥4-digit** cores are checked. When a figure isn't found, the
policy is **flag-and-warn** (show the answer, surface the figure as unverified),
not withhold/abstain. Result is surfaced in `/ask`, persisted (migration `0005`),
and shown as a warning banner in the reader.

**Why:** "No fabricated figures" is Mosaic's core promise and was defended only by
a prompt + `temperature=0` + a small eval (Vera's AT-RISK). The ≥4-digit threshold
keeps false positives down — small numbers, 2-digit percentages, and `10-K` collide
spuriously. Flag-and-warn (James's call) over hard-abstain because the one case the
digit-core method can't catch — a *re-scaled* figure ("383.3 billion" from a
"383,285 million" source, which would need unit-aware table parsing to match) — is a
false *negative-of-matching* that would otherwise wrongly nuke a correct answer; for
a personal-use tool, warning + deep-links to verify beats silently dropping a good
answer. Deliberately lightweight; not a general numeric-equivalence engine.

## 2026-06-18 — Project objective: personal portfolio + personal use (NOT a startup)

**Decision (James, CEO):** Mosaic's goals are (1) a tool James genuinely uses for
investment research, and (2) a recruiter-impressive portfolio piece. "Startup-capable /
defensibility / monetization" is explicitly DROPPED as a goal (per Vera's review: the
moat is thin and chasing it isn't worth it).

**Why:** Frees us to optimize for daily personal usefulness and for "a recruiter can
clone, run, and be impressed" — and to stop spending effort on moats, paid data, or
commercialization.

**How to apply:** Prioritize working software, clean-clone reproducibility, polish, and
the trust spine over any growth/moat work. This SUPERSEDES the "startup potential" goal
listed in the role manuals (`SALLY.md`, `VERA.md`) — future advisors should measure
against portfolio + personal use only.

## 2026-06-18 — Milestone 3 RAG stack: bge-small (384d) + section-aware chunks + RRF + Gemini Flash

**Decision:** The "Ask this filing" pipeline is: section-aware sub-chunks
(~3k chars, ~400 overlap, on paragraph boundaries, carrying absolute char
offsets) → local `BAAI/bge-small-en-v1.5` embeddings (384-dim, pgvector HNSW
cosine) → hybrid retrieval (pgvector semantic + Postgres full-text) fused with
Reciprocal Rank Fusion (k=60), pre-filtered to one filing → grounded answer from
**Gemini 2.0 Flash** behind an `app/llm` provider seam. `answer_cache` is keyed
by `(filing_id, question_hash, provider, model)` so swapping `LLM_MODEL` never
serves a stale answer from a different model. bge query/passage asymmetry is
honored: queries get the "Represent this sentence for searching relevant
passages:" instruction prefix, passages are embedded plain.

**Why:** All four seams chosen with James for the ~$0 goal (local embeddings =
no rate limits/cost; Gemini Flash free tier; RRF needs no score normalization
across the cosine/ts_rank scales). 384-dim keeps the index small and is locked
into migration 0004 — changing it requires a re-embed. Char offsets are
preserved end-to-end so citations deep-link into the immutable `content_text`.

## 2026-06-19 — Keyword retrieval: OR tsquery + drop the filing's own company name

**Decision (applied):** The full-text half of hybrid retrieval builds an **OR**
`to_tsquery` from the question's content terms (lowercased, stopworded), and also
drops the **filing's own company name** tokens. Recall@8 went 0.60 → **1.00**.

**Why:** AND semantics (`websearch_to_tsquery`) required every query term in one
chunk, so natural-language questions matched nothing — effectively semantic-only.
But OR alone didn't move the number: Postgres `ts_rank` has **no IDF**, so keeping
the company name ("apple") + ubiquitous terms rewarded chunks that merely repeat
common words over the chunk with the actual answer. In single-filing search the
company name is in nearly every chunk, i.e. pure noise — dropping it is what
recovered the answer chunks to rank 1–2. (Two remaining "misses" were a too-strict
golden key, not a retrieval failure — see eval note.)

## 2026-06-19 — Golden recall is multi-span; Gemini model pinned to what the key serves

**Decision:** (1) Golden Q&A recall is scored against **multiple** legitimate
answer spans per question, not one exact sentence. (2) Default `LLM_MODEL` is
**gemini-2.5-flash-lite**, not gemini-2.0-flash.

**Why:** (1) Inspection showed retrieval surfacing genuinely-correct passages at
rank 1–2 that a single-span key marked as misses (e.g. the income-tax note answers
"what affects the effective tax rate"). Allowing multiple relevant passages is
standard IR practice and reflects real answerability. (2) This project's key
returns `429 limit:0` for gemini-2.0-flash (not served); `client.models.list()`
shows the 2.5/3.x lineup. flash-lite is verified end-to-end. Free tier is
~20 req/day/model, so `answer_cache` is load-bearing, not a nicety. Also fixed:
grouped citations (`[1, 2]`) were silently dropped by a `[\d]`-only parser
(backend + UI) — they now parse, so answers aren't shown as uncited.

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
