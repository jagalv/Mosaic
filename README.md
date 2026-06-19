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
  README.md            # this file — onboarding: what/why + current status
  CLAUDE.md            # operating instructions auto-read by Claude Code (Alexander)
  docs/
    DESIGN.md          # full product + architecture vision
    ROADMAP.md         # milestone-based build plan (check boxes as you go)
    DECISIONS.md       # short dated log of real architectural choices
    WORKLOG.md         # shared AI hand-off log (read latest at start, append at end)
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

Full local stack: real SEC financials, a filing reader, and the "Ask this filing"
RAG demo — **browser → FastAPI → Postgres (pgvector) → browser**.

**Prerequisites:** Docker Desktop, Node 20+, Python 3.11+.

```bash
# 0. Env — copy the examples (real .env files stay gitignored)
cp .env.example .env                          # repo root (DB + API + LLM config)
cp apps/web/.env.local.example apps/web/.env.local

# 1. Database — start local Postgres (pgvector) and wait for it to be healthy
docker compose up -d
docker compose ps                             # STATUS should show "healthy"

# 2. Backend (services/api) — venv, deps, migrate
cd services/api
py -m venv .venv                              # Windows; use python3 on macOS/Linux
.venv/Scripts/activate                        # macOS/Linux: source .venv/bin/activate
# IMPORTANT: install CPU-only torch FIRST, or pip pulls the ~2.5GB CUDA wheel.
# (torch backs the local bge embedding model used by the RAG step.)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
alembic upgrade head                          # creates all schema (M0–M3)

# 2a. Ingest SEC data for the 10 starter companies (requires SEC_USER_AGENT in .env).
#     Caches raw EDGAR JSON/HTML to data/ so reruns don't re-hit SEC; idempotent.
python -m app.ingest.run                      # financials (companies/filings/financials)
python -m app.ingest.documents                # filing text + 10-K section segmentation
python -m app.ingest.chunk                    # M3: section-aware retrieval chunks
python -m app.ingest.embed                    # M3: local bge embeddings -> pgvector
pytest                                         # golden tests: numbers, sections, chunking, guard, Q&A

uvicorn app.main:app --reload --port 8000
# verify: curl http://localhost:8000/health        -> {"service":"ok","db":"ok"}
#         curl http://localhost:8000/company/aapl  -> pivoted financials JSON

# 3. Frontend (apps/web) — in a new terminal, from the repo root
npm install                                   # installs all workspaces (once)
npm run dev:web                               # http://localhost:3000
```

**For "Ask this filing":** set `GEMINI_API_KEY` in `.env` (free key:
<https://aistudio.google.com/apikey>). Without a key, set `LLM_PROVIDER=mock` to
exercise the full pipeline offline. The free tier is ~20 requests/day per model;
`answer_cache` absorbs repeats. The numbers guard flags any figure in an answer
that isn't found in the cited source text.

Open <http://localhost:3000> — you should see **API: ok / Database: ok**, sourced
through FastAPI from Postgres. Then open <http://localhost:3000/company/aapl> for
real multi-year SEC financials + a filing list; click a 10-K to read it with a
navigable section outline (Risk Factors, MD&A, …) and ask it a question with
cited, deep-linked answers.

To point at a hosted Postgres (Supabase/Neon) instead of Docker, set `DATABASE_URL`
in `.env` to the provider's connection string (keep the `+psycopg` driver prefix) —
no code changes needed.

---

## Status

🚧 **Phase 1 — Foundation & the Wedge.** See [`docs/ROADMAP.md`](docs/ROADMAP.md) for the live milestone tracker.

## Disclaimer

Mosaic is a research tool, not investment advice. Nothing it produces is a recommendation to buy or sell any security.
