# Mosaic — Build Roadmap

How to use this file: work top to bottom. Each **milestone** ends in something you can demo on screen. Check boxes as you go. Don't start a milestone before the one above it runs. Keep a one-line note in `DECISIONS.md` whenever you make a real architectural choice.

**Golden rule:** build *vertical slices* (one feature, top to bottom, ugly but working), never whole layers. Always keep `main` in a runnable state.

---

## Vera's reset — 2026-06-19 (read this first)

I reviewed the real repo at the M3 checkpoint. The build is strong and the wedge works. This
section recalibrates the plan to reality; the milestone list below is unchanged in *shape*, but
the estimates were fantasy-optimistic in the original (M3 was budgeted at 1.5–2 weeks and landed in
~2 days of AI-assisted work). Full assessment in `docs/STATUS.md`.

**What I changed and why:**
- Added a **Definition of Complete** (below) — the original roadmap never said what "done" means,
  so "done" had drifted to "passes on the dev machine." That's the gap that nearly shipped M3 with
  a repo no one else can run.
- Re-tagged effort estimates to **AI-assisted-solo reality** (focused-session sizes, not
  calendar weeks), while keeping honest buffers for the two things that actually eat time: messy
  data plumbing and the Gemini free-tier throttle.
- Added a **"Close-out M3" block** — M3 is ~95%, not done. The remaining 5% is reproducibility +
  two abstention checks + a clean commit, and it gates everything else.

**Definition of Complete (applies to every milestone from now on):**
A milestone is *done* only when **all** of these are true — not just "it works for me":
1. A **clean clone** (`git clone` → documented setup steps → run) starts and demos the feature.
   That means deps are pinned in `requirements.txt`/`package.json` and every new env var is in
   `.env.example`. ("Works in my venv" is not done.)
2. The feature's **trust claim is tested**, not just asserted (golden fixtures for numbers, golden
   Q&A for answers, a security test for access control).
3. **`main` is committed clean** — no pile of uncommitted changes, WORKLOG appended, ROADMAP boxes
   ticked, DECISIONS entry if a real choice was made.

**What "shippable" means for Mosaic, concretely:**
- **Demo-ready (≈0.5–1 focused session, basically here):** clean clone boots; a real cited answer
  on ≥2 companies verified live; M3 closed and committed clean. This is the portfolio screenshot.
- **v1 / portfolio-shippable (≈1–1.5 weeks):** the above + M4 (watchlists, notes, row-level
  security + the cross-user security test) so it's a *persistent personal tool*, not a stateless
  lookup + the "Make it presentable" block (public repo, README screenshots/GIF) + an expanded,
  honest eval (≥30 Qs / ≥5 companies, incl. numeric) and a runtime numbers guard + auth (deferred
  since M0, due before M4).
- **Personal-use real:** overlaps v1 — usable for your own research once notes/watchlists persist
  and the corpus is a bit wider.

**Honest completion estimate for Phase 1 v1:** ~**2–3 focused weeks** of calendar time at the
current cadence. The bulk of that is **M4's auth + RLS + security test** — the unglamorous,
must-be-correct plumbing this very roadmap warns is where projects stall (see "Where the time
really goes"). The AI features are the fast part; they're largely behind you.

### Close-out M3 (do before anything else — ≈1 focused session)
- [x] ~~Pin the M3 runtime deps~~ — **already pinned** (Vera read stale copies): `requirements.txt`
      has pgvector/sentence-transformers/google-genai; torch is a documented CPU-index pre-step.
      Verified on a clean venv (torch stayed `+cpu`, API imports, pytest 33/33).
- [x] ~~Add M3 env vars to `.env.example`~~ — **already present** (`GEMINI_API_KEY`, `LLM_MODEL`,
      `EMBEDDING_MODEL`). Confirmed by direct read.
- [x] **Clean clone boots** — fresh venv → CPU torch → `pip install -r requirements.txt` → API
      imports + full pipeline answers end-to-end (mock); pytest 33/33 on the clean venv. README
      install section smoothed (torch-first, chunk/embed steps, key/mock note).
- [x] **Runtime numbers guard** — `app/rag/guard.py`: any answer figure not found in retrieved
      text is flagged (flag-and-warn, shown in the reader). 8 tests; migration `0005` persists it.
- [x] **2 abstention checks** (`appstore-dau`, `msft-cfo-salary`) — both abstain. Faithfulness = 13/13.
- [x] **Live cited-answer check** — a real net-sales answer's footnotes resolve to the
      segment/income-statement source spans containing the figures; numbers guard passed (no
      false-fire on the correct figures).
- [ ] **Commit a clean tree** — first confirm `git status` in your own terminal is sane (sandbox
      shows phantom staged deletions = lag; verify before committing). *(only open M3 item)*

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
- [x] Auth wired up — sign up / log in *(done 2026-06-19: backend in M4a — `users` + argon2 + JWT
      httpOnly-cookie sessions + `get_current_user`; login/signup UI + server guard in M4d)*
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

### Milestone 3 — The wedge: "Ask this filing" ← ✅ DONE (2026-06-19)
This milestone proves the entire thesis. Spend real care here.

- [x] Section-aware chunking with metadata (`cik, accession_no, form_type, section, fiscal_period, char_range`)
- [x] Embed chunks (local `bge-small`/`e5-small`) → store in pgvector; never re-embed unchanged chunks (content hash)
- [x] Hybrid retrieval: pgvector semantic + Postgres full-text, fused (RRF), pre-filtered by company/form/section — *OR keyword + company-name strip; **recall@8 = 1.00**.*
- [x] Grounded answer endpoint: answer ONLY from retrieved context; cite chunk IDs; return "not stated in the filings" when unsupported — *verified: 10/10 answerable grounded+cited; abstains.*
- [x] AI panel UI: footnotes that deep-link to the source paragraph — *built, `next build` clean (grouped-citation deep-links handled).*
- [x] Build a golden Q&A set (10–20 questions with known answers + source spans) — *13 Qs (10 answerable, multi-span; 3 unanswerable), self-validating.*
- [x] Check faithfulness (every claim supported?) and retrieval recall@k before trusting it — *recall@8 = 1.00; **faithfulness = 13/13 = 1.00** (gemini-2.5-flash-lite): 10/10 answerable grounded with real citations, 3/3 unanswerable abstain.*
- [x] `ai_interactions` log: prompt, retrieved chunk IDs, latency, tokens, feedback
- [x] `answer_cache` for repeated questions per filing (key includes provider+model)
- [x] **Runtime numbers guard** (trust spine): flag any answer figure not found in the retrieved text (flag-and-warn; shown in the reader) — `app/rag/guard.py`, migration `0005`.

**Status: ✅ DONE.** `main` green (`pytest` 33/33 on dev **and** a clean venv; `next build` clean; clean-clone boot + full migration chain verified on an empty DB). **recall@8 = 1.00**; **faithfulness = 13/13 = 1.00** (gemini-2.5-flash-lite): 10/10 answerable grounded with real citations, 3/3 unanswerable abstain. Trust spine has a runtime numbers guard (verified live: correct figures pass, no false-fire). Live check: a real net-sales answer's footnotes deep-link to the segment/income-statement spans that contain the cited figures. Only open item is James's clean commit (sandbox git lag — verify `git status` in a real terminal first).

**Demo:** ask a real question about a real filing, get a cited answer that links to the source. This is the "oh, that's actually useful" moment.

### Milestone 4 — It's an OS, not a lookup (≈1 week)
- [x] `watchlists` + `watchlist_items`, tied to the logged-in user — *backend (M4b) + UI (M4d): /watchlist manager + company "Watch" popover*
- [x] Persistent `notes` (per company / per filing) — *backend (M4c): per-target company/filing
      (CHECK exactly-one), RLS forced + fail-closed owner policy; UI (M4d): inline NotesPanel on
      company + filing pages, plus the /notes index*
- [x] Row-level security so a user only ever sees their own data — *real Postgres RLS, FORCED, via
      non-superuser `mosaic_app` role + `set_config` GUC (M4b; superuser-bypass fixed in migration 0008)*
- [x] Security test: one user cannot read another user's rows — *`tests/test_rls.py`: DB + API
      isolation, fail-closed, no pooling leak, commit-contract — now covers watchlists AND notes*

**Demo:** come back the next day and your research, watchlist, and notes are all still there.

### End of Phase 1 — Make it presentable
- [x] **Design-system + visual polish pass** (2026-06-19) — Linear/Vercel-grade modern fintech,
      teal accent, dark-first; app shell, restyled hero/dashboard/company/reader, loading/error/404
      states. See DECISIONS 2026-06-19 "Design system". (Trust spine preserved + verified.)
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
