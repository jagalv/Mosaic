# Mosaic

**An AI-powered investment research operating system.** Mosaic is a research workspace where you pull up any public company and get a structured, citation-backed view — fundamentals, SEC filings, risk, and an AI layer that reads filings and earnings transcripts *for* you and answers questions with footnotes that link to the exact source paragraph.

> *Mosaic theory* is how analysts build a legitimate investment view by assembling many individually-public pieces of information. That's what this product does.

---

## Why it exists

Serious fundamental research lives in a painful gap. Free tools (Yahoo Finance, generic chatbots) are shallow or hallucinate. Professional tools (Bloomberg, FactSet, CapIQ) cost thousands a year. The actual work — reading a 200-page 10-K, finding the risk factors that changed, pulling the right line items, comparing peers, writing it up — is slow and badly served.

Mosaic compresses hours of filing-reading into minutes **without sacrificing trust**, because every AI claim is grounded in and linked to a primary source.

## The killer feature: "Ask this filing"

Type a ticker, land on a company page, and ask natural-language questions answered *only* from that company's SEC filings and transcripts — with inline citations linking to the exact paragraph. Example: *"How did their risk factors change between the 2023 and 2024 10-K?"*

## What makes it different

- **vs. ChatGPT/Perplexity** — Not a chat box over the open web. RAG over a curated corpus of actual SEC filings + structured financials, so answers are grounded, current, and cite the source paragraph.
- **vs. Yahoo/Koyfin** — Those are dashboards. Mosaic adds the reading/reasoning layer *and* persistent personal knowledge (memos, notes, watchlists as first-class objects).
- **vs. Bloomberg/FactSet** — A fraction of the cost, AI-native, built for the workflow of *forming a thesis*.

---

## Tech stack

| Layer | Choice | Why |
|---|---|---|
| Frontend | Next.js (App Router) + TypeScript + Tailwind + shadcn/ui | Product/UX surface; Server Components for data-heavy pages |
| AI/Data service | Python + FastAPI | SEC ingestion, XBRL parsing, embedding, RAG orchestration |
| Database | Postgres + pgvector | Relational + vector + full-text in one DB — deliberately not over-engineered |
| Object storage | Cloudflare R2 / Supabase Storage | Raw filings + generated artifacts |
| Auth | Supabase Auth / Clerk | JWT sessions + row-level security |
| LLM | Gemini Flash / Groq (cheap-first, swappable) | Most work is summarize/extract/answer — small models suffice |
| Embeddings | Local `bge-small` / `e5-small` | Keeps embedding at $0, no rate limits during bulk ingestion |
| Hosting | Vercel + Supabase/Neon + Fly.io/Render | All free tiers; target operating cost ~$0/month |

## Data sources

SEC EDGAR (submissions + companyfacts XBRL — the backbone), Yahoo Finance (`yfinance`), Financial Modeling Prep free tier, FRED (macro), Polygon free tier (optional). All access goes through a thin source-abstraction layer so any single free source can be swapped without touching the app.

---

## Repo structure

```
mosaic/
  README.md            # this file
  docs/
    DESIGN.md          # full product + architecture vision
    ROADMAP.md         # milestone-based build plan (check boxes as you go)
    DECISIONS.md       # short dated log of real architectural choices
  apps/
    web/               # Next.js frontend
  services/
    ingest/            # Python: SEC pipeline, parsing, embedding
    api/               # Python FastAPI: RAG + AI endpoints
  packages/
    shared/            # shared types/config
  .env.example         # documented env vars (NO secrets)
```

## Running locally

Milestone 0 skeleton: a health check that flows **browser → FastAPI → Postgres → browser**.

**Prerequisites:** Docker Desktop, Node 20+, Python 3.11+.

```bash
# 0. Env — copy the examples (real .env files stay gitignored)
cp .env.example .env                          # repo root (DB + API config)
cp apps/web/.env.local.example apps/web/.env.local

# 1. Database — start local Postgres (pgvector) and wait for it to be healthy
docker compose up -d
docker compose ps                             # STATUS should show "healthy"

# 2. Backend (services/api) — venv, deps, migrate, run
cd services/api
py -m venv .venv                              # Windows; use python3 on macOS/Linux
.venv/Scripts/activate                        # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head                          # enables pgvector + creates health_check
uvicorn app.main:app --reload --port 8000
# verify: curl http://localhost:8000/health  -> {"service":"ok","db":"ok"}

# 3. Frontend (apps/web) — in a new terminal, from the repo root
npm install                                   # installs all workspaces (once)
npm run dev:web                               # http://localhost:3000
```

Open <http://localhost:3000> — you should see **API: ok / Database: ok**, sourced
through FastAPI from Postgres.

To point at a hosted Postgres (Supabase/Neon) instead of Docker, set `DATABASE_URL`
in `.env` to the provider's connection string (keep the `+psycopg` driver prefix) —
no code changes needed.

---

## Status

🚧 **Phase 1 — Foundation & the Wedge.** See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the live milestone tracker.

## Disclaimer

Mosaic is a research tool, not investment advice. Nothing it produces is a recommendation to buy or sell any security.
