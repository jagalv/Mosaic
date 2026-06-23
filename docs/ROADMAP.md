# Mosaic — Build Roadmap

How to use this file: work top to bottom. Each **milestone** ends in something you can demo on screen. Check boxes as you go. Don't start a milestone before the one above it runs. Keep a one-line note in `DECISIONS.md` whenever you make a real architectural choice.

**Golden rule:** build *vertical slices* (one feature, top to bottom, ugly but working), never whole layers. Always keep `main` in a runnable state.

---

## Vera's Phase-2 reset — 2026-06-22 (read this first)

Phase 1 (M0–M4 + the design-system pass) is **substantively done and genuinely strong** — the
wedge works, the trust spine has a real numbers guard, and M4 shipped DB-enforced RLS with a true
security test. Full assessment in `docs/STATUS.md` (2026-06-22). The old milestone list is now
exhausted, so this is its replacement: a forward plan optimized for the **locked goals — personal
research tool + recruiter-impressive portfolio, at ~$0**. Startup/defensibility is de-prioritized
per DECISIONS 2026-06-18, so anything that only served *monetization or a sharing product* is cut.

**How I re-scored the old Phase 2–4 grab-bag (each item kept / reordered / cut, with a reason):**

| Old item | Verdict | Why |
|---|---|---|
| Expand company universe (S&P 100) | **KEEP → M6** | Directly serves personal-use; cheap (pipeline exists); enables diffs/screener. |
| Research workspace: memos/tags/thesis | **KEEP → M8** | The capstone "OS" feature and a standout portfolio artifact. Reframed as the cited-memo milestone. |
| Cross-filing diffs ("what changed") | **KEEP → M7, flagship** | Most differentiated + personally useful AI feature; it's the README's own headline example. |
| Side-by-side multi-company comparison | **DEFER → Phase 3** | Useful but lower differentiation than diffs/memo; cheap once corpus is wide. |
| Fundamentals screener | **DEFER → Phase 3** | Personally useful; depends on a wide corpus (M6); modest portfolio lift. |
| Earnings-transcript ingestion | **WEIGH → Phase 3** | Real value + README promise, but $0-clean sourcing is a risk — validate a free source first. |
| FRED macro dashboard | **OPTIONAL → Phase 3** | Easy + free, nice breadth, but off the core filing-research thesis. Small side-quest. |
| Investment-memo generation | **KEEP → M8** | See workspace above. |
| Portfolio/CSV import | **CUT (for now)** | Low portfolio differentiation; only marginal personal-use vs. notes/watchlists. |
| Retrieval re-ranking (cross-encoder) | **DEFER (conditional)** | Don't build speculatively — recall is already 1.00 on the (small) set. Revisit only if M6's wider eval shows a precision problem. |
| Perf/cost hardening | **FOLD into M5** | Not a standalone milestone; handle at deploy + as-needed. |
| Sharing / public cited memos | **CUT** | A product/startup feature; off-goal. |
| Learning layer (explainers/templates) | **CUT** | Product polish, low leverage for the locked goals. |
| Alerts via scheduled job | **CUT (for now)** | Operationally heavy at $0 (needs always-on scheduler); low portfolio lift. |
| Optional paid-tier gating | **CUT** | Monetization; explicitly off-goal. |

**Definition of Complete (every milestone, carried forward from the M3 reset):**
A milestone is *done* only when all are true: (1) a **clean clone** runs and demos it (deps pinned,
env vars in `.env.example`); (2) its **trust/security claim is tested**, not just asserted; (3)
**`main` is committed clean** with WORKLOG appended, ROADMAP ticked, DECISIONS entry if a real
choice was made. **New for Phase 2:** for a portfolio milestone, "done" also means it's **pushed
and visible** (the live demo reflects it).

**Effort estimates** are AI-assisted-solo "focused sessions" (a session ≈ a few hours of real
work), calibrated to actual cadence — M3 and M4 each landed in ~1–2 focused days. Honest buffers
included for data-plumbing and free-tier friction.

**Sequencing at a glance:** **M5 (ship) → M6 (corpus + eval) → M7 (cross-filing diffs) → M8 (cited
memo)**, then optional Phase-3 breadth. The two highest-leverage milestones are **M5** (converts
the build into a visible portfolio piece — do it first) and **M7** (the flagship feature that best
showcases the whole stack, gated on M6).

---

## ✅ Phase 1 — Foundation & the Wedge (M0–M4) — COMPLETE

Delivered: M0 skeleton · M1 SEC financials · M2 filings + 10-K segmentation · M3 the wedge
("Ask this filing": grounded, cited, **numbers-guarded** Q&A — recall@8 = 1.00, faithfulness =
13/13) · a design-system polish pass (Linear/Vercel-grade, teal/dark, app shell, states) · M4 auth
(argon2 + JWT httpOnly cookies) + watchlists + notes + **DB-enforced Postgres RLS** (non-superuser
`mosaic_app` role) + a cross-user security test (DB + API). `pytest` green (confirm count in your
terminal — claimed 47, RLS suite needs local Postgres). Full per-milestone detail is preserved in
git history and DECISIONS; the old checkbox list lived here through 2026-06-19 and is now closed.

**The one Phase-1 loose end → folded into M5:** the "Make it presentable" block (public repo,
README screenshots/GIF) was never finished. It's the first thing M5 closes.

---

## Phase 2 — Deepen the wedge into its best self

The theme: stop adding surface area; make the thing that already works **visible, trustworthy at
scale, and genuinely useful for real research.**

### Milestone 5 — Ship & Showcase  ★ HIGHEST LEVERAGE — do this first (≈1–2 sessions)
Turn the finished build into a portfolio piece people can see and click. This is mostly packaging
and ops, not new engineering, and it unlocks the career goal immediately.

- [x] `git push` M4 to GitHub; `main` clean + current (done 2026-06-22).
- [ ] Set a real `AUTH_SECRET_KEY` (and rotate the `mosaic_app` password) for anything non-local.
      *(Real local AUTH_SECRET_KEY already set; rotation is for the hosted demo.)*
- [x] **Make the repo public** (github.com/jagalv/mosaic, 2026-06-22).
- [~] README: short "what this is" + screenshots + highlights — *done EXCEPT the AI-answer
      money-shot (Gemini was down) and an optional ~30s GIF. Grab the cited-answer shot when Gemini
      cooperates.*
- [x] Write up 2–3 `DECISIONS`-style highlights in the README (RLS superuser-bypass catch, numbers
      guard, RRF retrieval) (done 2026-06-22).
- [ ] **Live $0 demo:** deploy web (Vercel free) + API + Postgres (Neon/Supabase free tier), seeded
      with the current corpus. Set `AUTH_COOKIE_SECURE=true` behind HTTPS; lock CORS to the real
      origin.

**The genuinely hard part:** first real deploy always has friction — cross-origin cookies over
HTTPS (Secure flag, SameSite, CORS allow-credentials with a specific origin), cold hosted Postgres
+ the migration chain + the `mosaic_app` role on a managed DB, and the Gemini free-tier quota on a
*public* endpoint (consider a per-IP rate limit or a "demo mode" cap so one visitor can't exhaust
the day's quota).
**Definition of complete:** a stranger can open a URL, browse a real company, ask a filing a
question, and see a cited answer deep-link to the source — without you in the room — and the public
repo's README shows it at a glance.
**Demo:** the link itself.

### Milestone 6 — Corpus + Evidence (≈2–3 sessions) — depends on: M5 deploy target exists
Widen the two things that are currently thin: how many companies you can research, and how
trustworthy the headline numbers are.

- [ ] Expand the company universe (S&P 100 first, then grow) via the existing ingestion pipeline;
      handle the XBRL/segmentation edge cases that show up beyond the 10 starters.
- [ ] Ingest **≥2 years of 10-Ks per company** (prerequisite for diffs in M7).
- [ ] Expand the golden Q&A set to **≥30 questions across ≥5–8 companies**, including **numeric**
      questions (exercise the guard) and at least a few that *should* abstain.
- [ ] Re-run recall@k + faithfulness on the wider set; record the honest numbers (they may dip
      below 1.00 — that's fine and more credible than a suspicious perfect score on 13 Qs).
- [ ] Add lightweight retrieval/answer **observability** you'd actually look at (the `ai_interactions`
      log exists — surface a tiny internal view or a summary query: abstention rate, guard-flag
      rate, latency).

**The genuinely hard part:** authoring verified answer-spans at scale is real grind (the spans must
exist verbatim in the filing); and wider data surfaces messier XBRL/HTML than the 10 clean
starters did — expect data-plumbing days, not AI days.
**Definition of complete:** S&P-100-scale corpus with ≥2yr of 10-Ks; an honest eval over ≥30 Qs /
≥5–8 companies committed with its real (not cherry-picked) scores.
**Demo:** ask the same kind of question across a dozen different companies and get cited answers;
show the eval report.

### Milestone 7 — Cross-filing diffs: "what changed since last year"  ★ flagship feature (≈3–4 sessions) — depends on: M6 (≥2yr corpus)
The single most differentiated, demoable, *and* personally useful AI feature on the list — and it's
the README's own headline example. This is the one that makes a technical reviewer lean in.

- [ ] Align comparable sections across two filings of the same company/form (e.g. FY2024 vs FY2023
      Item 1A Risk Factors) using the existing `filing_sections` + char offsets.
- [ ] Produce a **grounded, cited diff**: what was added / removed / materially reworded, each side
      linking to its source span — *not* a raw text diff; a readable "here's what changed and why it
      matters," still under the cite-or-abstain + numbers-guard contract.
- [ ] UI: a side-by-side or change-summary view with deep links into both filings.
- [ ] Golden test for the diff on a known pair (assert a real, known change is surfaced and a known
      non-change is not).

**The genuinely hard part:** semantic (not textual) diffing that stays grounded — section alignment
across years where headings/order drift, and summarizing change without hallucinating significance.
This is where the trust spine gets its hardest test; hold the line on grounding.
**Definition of complete:** pick a company, pick two years, get a cited summary of what changed in
the risk factors (or MD&A) that a human can verify from the linked sources.
**Demo:** "How did Apple's risk factors change from 2023 to 2024?" → a cited, verifiable answer.

### Milestone 8 — Cited investment memo (the research-OS capstone) (≈3–5 sessions) — depends on: M6, M7
The crown of the "research operating system" vision: generate a structured, **fully cited**,
human-editable memo on a company — pulling financials, filing answers, and (if present) cross-year
changes into one thesis object that lives in the workspace. Leans on everything already built.

- [ ] A `memo` / `thesis` object (per company, owned by the user, under RLS like notes/watchlists).
- [ ] Structured generation (e.g. Business / Financials / Risks / What-changed), every claim cited
      to a filing span or a financial line item; the **numbers guard extended to multi-paragraph
      prose** (no figure that isn't sourced).
- [ ] Human-in-the-loop editing (it drafts; you correct and keep) — the memo is yours, not the
      model's.
- [ ] Save to the workspace; viewable/editable later (persistence + RLS).

**The genuinely hard part:** keeping a *long, multi-section* generation faithful — long outputs are
where grounding decays and the guard matters most; and a genuine human-edit/version workflow, not a
one-shot dump.
**Definition of complete:** generate a cited draft memo for a company, edit it, reload tomorrow and
it's still there with every figure traceable to a source.
**Demo:** "Draft me a cited research memo on NVDA" → a structured, sourced, editable memo you'd
actually keep.

---

## Phase 3 — Breadth (optional, demand-driven; pick what you'd actually use)

Only after Phase 2. Each is independently valuable; none is load-bearing. Sequence by what *you*
want for personal research vs. what rounds out the portfolio.

- [ ] **Side-by-side multi-company comparison** (cheap once corpus is wide; good demo).
- [ ] **Fundamentals screener** over the cached universe (personally useful; modest portfolio lift).
- [ ] **Earnings-transcript ingestion** — *first validate a genuinely free, clean source* (the $0
      constraint is the risk here); then it flows through the same RAG/guard spine. Honors the
      README promise and widens the corpus beyond filings.
- [ ] **FRED macro layer** (rates/yield-curve/CPI + an AI macro digest) — free API, easy, nice
      breadth; off the core thesis, so treat as a small side-quest.
- [ ] **Retrieval re-ranking (cheap cross-encoder)** — *conditional:* build only if M6's wider eval
      reveals a real precision problem. Don't pre-optimize a metric that's currently 1.00.

---

## What I cut, and why (so it's a decision, not an omission)
- **Sharing / public cited memos**, **paid-tier gating** — product/monetization features; off the
  locked goals (startup de-prioritized).
- **Learning layer**, **portfolio/CSV import**, **alerts/scheduler** — low leverage for personal-use
  + portfolio at $0, or operationally heavy at $0. Revisit only if the goals change.
  *(Any of these is a one-line un-cut if James decides otherwise — surfacing, not deciding.)*

## A strategic choice for James (I'm flagging, not deciding)
After M5+M6, the flagship feature order is **M7 (diffs) then M8 (memo)**. If your priority is the
*single most impressive demo*, M8 (a cited memo) is the bigger "wow"; if it's the *most defensible,
verifiable* showcase of the trust spine, M7 (diffs) is safer and lands sooner. I sequenced
M7→M8 (diffs are an input to a good memo, and the lower-risk build first), but the order is yours.

---

## Where the time really goes (unchanged truth, still true)
The AI features come together faster than expected. The grind is the unglamorous plumbing — messy
SEC HTML, inconsistent XBRL, rate limits, auth/permissions, and now **first-deploy ops** (hosted DB
+ migrations + cross-origin auth). Phase 2's hardest days are deploy days and data-breadth days, not
model days. Expect it; it's where similar projects stall.

## Prompting your AI assistant — quick reference
- **You're the architect/reviewer; the AI is a fast, overconfident junior engineer.** Give scoped jobs, check the work.
- **Point it at context first:** the relevant doc + existing files, then the task.
- **One vertical slice per prompt.** Concrete and reviewable.
- **Match style to risk:** boilerplate/UI/CRUD/tests → prompt freely, skim-review; grounding/RAG glue/numbers/auth/RLS → go slow, read every line.
- **Verify financial/AI output against reality** — golden fixtures for numbers, golden Q&A for answers. "Looks right" is untrustworthy for any number on screen.
- **Use it as a reviewer** before merging; **ask for trade-offs, not answers** on real decisions.
- Stay the human who understands every important part.
