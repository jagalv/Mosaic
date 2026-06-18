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
