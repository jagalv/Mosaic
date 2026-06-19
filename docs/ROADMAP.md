# Mosaic — Build Roadmap

How to use this file: work top to bottom. Each **milestone** ends in something you can demo on screen. Check boxes as you go. Don't start a milestone before the one above it runs. Keep a one-line note in `DECISIONS.md` whenever you make a real architectural choice.

**Golden rule:** build *vertical slices* (one feature, top to bottom, ugly but working), never whole layers. Always keep `main` in a runnable state.

---

## Phase 1 — Foundation & the Wedge

The goal of Phase 1 is a genuinely valuable, demoable product: research a few hundred companies end-to-end and get cited answers from their filings. Reach the hard, differentiating feature (Milestone 3) as early as is sane.

### Milestone 0 — Skeleton that runs (a few days)
Get the boring infra green *before* writing features. It's demoralizing to fight deploys later with real code at stake.

- [x] Initialize git repo (committed locally — push to GitHub still pending)
- [x] Set up monorepo structure (`apps/web`, `services/`, `packages/`, `docs/`)
- [x] `.gitignore` (node_modules, `.env`, `__pycache__`, `data/`) and `.env.example`
- [x] Postgres running locally (Docker + pgvector), connection verified `DB: ok`
- [x] Local loop works: browser → FastAPI → Postgres → browser (health check green)
- [ ] **DEFERRED →** Next.js app deployed to Vercel (intentionally out of scope for the local-pipeline session)
- [ ] **DEFERRED →** Auth wired up — sign up / log in (intentionally deferred; do before Milestone 4)
- [x] Push repo to GitHub (`jagalv/mosaic` — make public once presentable)

**Status:** Local skeleton ✅ green and committed. Vercel deploy + auth consciously deferred — not blockers for Milestone 1.

**Demo:** local health check shows **API: ok / Database: ok** end-to-end.

### Milestone 1 — One company, real data (≈1 week)
- [x] Pick ~10 companies (e.g. AAPL, MSFT, NVDA…) to start
- [x] SEC ingestion for just these: pull submissions + companyfacts (XBRL) → store in Postgres
- [x] Define core schema: `companies`, `financials`, `filings`
- [x] Set descriptive `User-Agent` for EDGAR; respect ~10 req/s
- [x] Company page renders: name, sector, multi-year financial-statements table
- [x] Golden fixture test: assert known financial values for a known filing

**Demo:** real SEC financial data rendering on a real company page. No AI yet.

### Milestone 2 — Filings on the page (≈1 week)
- [x] Fetch + store recent 10-K / 10-Q filings for the starter companies (raw text → Postgres; R2 deferred — see DECISIONS)
- [x] `filing_sections` table; segment filings by structure (Item 1A Risk Factors, Item 7 MD&A, etc.) — 10-K; 10-Q text stored, sectioning deferred
- [x] Filing list on the company page
- [x] Filing reader view with navigable sections

**Demo:** you can read a filing inside your app, jump to Risk Factors / MD&A.

### Milestone 3 — The wedge: "Ask this filing" ← THE IMPORTANT ONE (≈1.5–2 weeks)
This milestone proves the entire thesis. Spend real care here.

- [ ] Section-aware chunking with metadata (`cik, accession_no, form_type, section, fiscal_period, char_range`)
- [ ] Embed chunks (local `bge-small`/`e5-small`) → store in pgvector; never re-embed unchanged chunks (content hash)
- [ ] Hybrid retrieval: pgvector semantic + Postgres full-text, fused (RRF), pre-filtered by company/form/section
- [ ] Grounded answer endpoint: answer ONLY from retrieved context; cite chunk IDs; return "not stated in the filings" when unsupported
- [ ] AI panel UI: streams the answer with footnotes that deep-link to the source paragraph
- [ ] Build a golden Q&A set (10–20 questions with known answers + source spans)
- [ ] Check faithfulness (every claim supported?) and retrieval recall@k before trusting it
- [ ] `ai_interactions` log: prompt, retrieved chunk IDs, latency, tokens, feedback
- [ ] `answer_cache` for repeated questions per filing

**Demo:** ask a real question about a real filing, get a cited answer that links to the source. This is the "oh, that's actually useful" moment.

### Milestone 4 — It's an OS, not a lookup (≈1 week)
- [ ] `watchlists` + `watchlist_items`, tied to the logged-in user
- [ ] Persistent `notes` (per company / per filing)
- [ ] Row-level security so a user only ever sees their own data
- [ ] Security test: one user cannot read another user's rows

**Demo:** come back the next day and your research, watchlist, and notes are all still there.

### End of Phase 1 — Make it presentable
- [ ] Make the repo public
- [ ] Polish README; add screenshots / a short GIF
- [ ] Fill in the "Running locally" section with real steps
- [ ] Write up 2–3 `DECISIONS.md` entries explaining key choices

---

## Phase 2 — Becomes an OS (paced over weeks)
- [ ] Expand the company universe (start with S&P 100, grow from there)
- [ ] Research Workspace: memos, tags, "thesis" objects linking companies + filings + your writing
- [ ] Cross-filing diffs: "what risk factors changed since last year"
- [ ] Side-by-side multi-company comparison
- [ ] Basic fundamentals screener over the cached universe
- [ ] Alerts (new filing / large price move) via a scheduled job — keep it simple (idempotent cron diff checks)

## Phase 3 — AI Leverage & Market Context
- [ ] Investment memo generation (structured, fully cited, human-edited) → into the Research Workspace
- [ ] Earnings-transcript ingestion + analysis
- [ ] FRED macro dashboard (rates, yield curve, CPI, employment, spreads) + AI macro digests
- [ ] Portfolio tracking via CSV import (performance, allocation, exposure)

## Phase 4 — Polish, Scale & Product
- [ ] Sharing / public cited memos ("GitHub for analysis")
- [ ] Learning layer (inline explainers, guided research templates)
- [ ] Retrieval re-ranking (cheap cross-encoder) where precision needs it
- [ ] Performance + cost hardening
- [ ] Optional paid-tier gating

---

## Where the time really goes (so you plan for it)
The AI features come together faster than expected. The grind is the unglamorous plumbing — parsing messy SEC HTML, mapping inconsistent XBRL tags to clean line items, rate limits, auth/permissions. Phase 1's hardest days are **data-pipeline days, not AI days**. That's normal and it's where similar projects stall. Expect it; don't read it as failure.

## Prompting your AI assistant — quick reference
- **You're the architect/reviewer; the AI is a fast, overconfident junior engineer.** Give scoped jobs, check the work.
- **Point it at context first:** the relevant doc + existing files, then the task. "Add X consistent with this schema and this file" beats a cold "build X."
- **One vertical slice per prompt.** Concrete and reviewable, not "build the backend."
- **Match style to risk:**
  - *Boilerplate / UI / CRUD / tests* → prompt freely, skim-review. High speed, low risk.
  - *Grounding prompt, RAG glue, anything touching numbers users see, auth/RLS, caching* → go slow, ask it to explain its approach first, read every line.
- **Make it reason before it writes** for anything non-trivial.
- **Verify financial/AI output against reality** — golden fixtures for numbers, golden Q&A set for answers. "Looks right" is untrustworthy for any number on screen.
- **Use it as a reviewer** — before merging a branch, ask it to review the diff for bugs, security, edge cases.
- **Ask for trade-offs, not answers**, on real decisions — you learn the domain, which is half the point.
- Resist generating huge swaths at once just because it's fast. Stay the human who understands every important part.
