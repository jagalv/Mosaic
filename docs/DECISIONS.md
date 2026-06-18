# Decisions

A short, dated log of real architectural choices. Newest first. One entry per
genuine decision — not a changelog.

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
