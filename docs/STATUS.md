# Mosaic — Independent Status Assessment

**Author:** Vera (independent strategic & technical advisor)
**Date:** 2026-06-22
**Checkpoint:** End of Phase 1 — Milestones 0–4 complete + design-system polish
**Previous assessment:** 2026-06-19 (end of M3). This is a diff against that.
**Basis:** Direct host-file reads of the real repo — `app/rag/*` (incl. the new `guard.py`),
`app/auth.py`, `app/rls.py`, migrations 0005–0009, `tests/test_rls.py`, the frontend `(app)`
route group + gating, README, ROADMAP, DECISIONS, WORKLOG. Runtime claims (pytest, live demo,
push/public state) flagged for James to confirm in his own terminal. *Note: the sandbox `bash`/git
view lagged the real files badly this session — e.g. it showed an old `requirements.txt`; the host
reads are the source of truth, and they're good.*

---

## Overall verdict

**Phase 1 is, in substance, done — and it's genuinely strong work. The build is no longer the
question; the showcase is.** Every concern from my M3 review was addressed, not papered over:

- The **numbers guard** I called the #1 trust gap is built (`app/rag/guard.py`), wired into the
  answer path *and the cached path* (`routers/ask.py`), tested, and surfaced in the reader. The
  spine's thinnest point now has code behind it, not just a prompt.
- The **clean-clone hole** is closed: `requirements.txt` pins pgvector/sentence-transformers/
  google-genai/argon2/PyJWT with the CPU-torch pre-step documented; `.env.example` is complete
  (APP_DATABASE_URL, AUTH_SECRET_KEY, the RAG vars). The README setup now matches reality.
- **M4** delivered the hard, must-be-correct milestone cleanly: argon2 + JWT httpOnly-cookie auth,
  **DB-enforced Postgres RLS** via a non-superuser `mosaic_app` role, and a real cross-user
  security test. This is the part most solo projects fake or skip. It isn't faked here.

What remains is not engineering — it's **shipping**: the repo is still private, there's no live
demo URL, no screenshots/GIF, and (per Bobby's last WORKLOG) M4 may not be pushed yet. A portfolio
piece nobody can see or click is worth a fraction of its real quality. That gap, plus a thin
evidence base (13 evals / 2 companies) and a thin corpus (10 companies), is the whole story now.

**One-line verdict:** the work earned an A; the *presentation* is still a C, and closing that is
the highest-leverage thing left in Phase 1.

---

## Dimension scorecard (diffed vs M3, 2026-06-19)

### Product & vision — ON-TRACK (was on-track) — unchanged, delivered
The wedge now lives inside a real workspace: watchlists, notes, a gated personal area over a public
browse experience. That's the "OS, not a lookup" promise from the roadmap actually shipped, not
sketched. No scope creep — M4 was always on the plan. The public-browse / gated-workspace split
(`app/(app)/layout.tsx`: browse is public, personal pages self-guard) is exactly right for a
portfolio demo — a recruiter sees value before any signup wall. *Evidence: `(app)` route group,
`server-api.ts` cookie-forwarding, `notes-panel.tsx` anonymous→"log in to add notes".*

### Technical architecture — ON-TRACK (was on-track) — strengthened
The RLS implementation is the standout: `ENABLE` + `FORCE` (owner-bypass closed), a dedicated
`NOSUPERUSER NOBYPASSRLS` role, fail-closed GUC (`NULLIF(current_setting(...),'')::int` → no rows),
both `USING` and `WITH CHECK`, child-table policy keyed through parent ownership, and a documented
**commit contract** (`app/rls.py`: the dependency is the sole committer so a mid-handler commit
can't clear the transaction-scoped GUC). That is senior-grade and rare. Seams from M3 still hold.
One honest nit: architectural *breadth* (auth, RLS, RAG, ingest, design system) now slightly
outpaces *depth* (10 companies, 13 evals) — appropriate for a portfolio build, but the depth is
where the next leverage is. *Evidence: migrations 0007–0009, `app/rls.py`.*

### AI / trust quality — ON-TRACK (was **AT-RISK**) — ⬆ upgraded, the key improvement
The structural gap is closed. `guard.py` verifies every ≥4-digit figure in an answer traces to the
retrieved text (digit-core substring match), flag-and-warns rather than silently withholding, and
documents its own blind spot (a *re-scaled* "383.3 billion" vs a source "383,285 million" won't
match without unit-aware parsing). cite-or-abstain holds; abstain-without-LLM on empty retrieval;
faithfulness now **13/13** with all 3 unanswerable questions abstaining. I'm upgrading this to
on-track because the spine is now enforced in code, not just prompted. **The caveat that keeps it
honest:** the eval base is still tiny — 13 questions over **2 companies** (AAPL/MSFT). recall@8 =
1.00 and faithfulness = 1.00 should read as "no failures observed yet," not "robust." To *stay*
on-track as the corpus grows, the eval must widen (see plan M6). *Evidence: `guard.py`,
`answer.py`, `tests/golden_qa.json`, `routers/ask.py`.*

### Execution & velocity — ON-TRACK (was on-track) — the team responded to review
M4 — the security milestone — landed cleanly, and notably the team *acted on my M3 findings*
(pinned deps, built the guard, closed faithfulness). The three-AI/WORKLOG protocol is working as
designed: M4b's own security test **caught its own superuser-bypass bug**, which DECISIONS records
honestly and migration 0008 fixes. A process that catches its own security holes is the process
working. *Evidence: DECISIONS 2026-06-19 M4 amendment, WORKLOG M4 entries.*

### Cost & operations — ON-TRACK (was on-track) — but the question is shifting
Still $0: local bge embeddings, Gemini free tier, local Postgres, free EDGAR; no paid service in
`.env.example`. The forward watch: the Gemini free tier (~20 req/day/model) is a real ceiling for a
*live public demo* — a recruiter poking a deployed app could exhaust it in a sitting (answer_cache
helps for repeats, not first-time questions). And there's still no hosted deploy. The question is
moving from "is it $0?" (yes) to "can it be $0 *and* publicly demoable?" — answerable yes (Vercel +
Neon/Supabase free tiers), but it's unbuilt work. *Evidence: `.env.example`, `gemini.py`.*

### Risk — AT-RISK (reframed; defensibility de-prioritized per charter) — what the risk now *is*
Startup/defensibility is no longer a goal, so the relevant risk isn't "a competitor out-builds the
moat." It's **the artifact under-selling itself**: (1) demo fragility — no live URL, free-tier
quota, dev-placeholder `AUTH_SECRET_KEY`; (2) thin corpus + eval making genuinely impressive
engineering look smaller than it is under scrutiny. Both are fixable and both are about
*presentation of quality*, not quality itself. *Evidence: ROADMAP "Make it presentable" (3 of 4
unchecked), 10-company corpus, 13-question eval.*

### Career value — ON-TRACK, rising (was on-track w/ packaging gap) — ⬆ trajectory
The work is now demonstrably senior across exactly the surfaces the goal names: grounded RAG with a
real trust spine *and a numbers guard*, DB-enforced RLS with a security test, from-scratch auth,
full-stack with a polished design system. The M3 packaging gap is *half* closed (README is
clean-clone-able; the UI is Linear/Vercel-grade). The other half — **make it visible** — is now
THE career lever: private repo, no live URL, no screenshots/GIF, AUTH_SECRET_KEY placeholder, maybe
unpushed. The build is done; the showcase isn't. *Evidence: DECISIONS design-system entry, README,
WORKLOG (push pending).*

---

## Goal alignment (locked: personal-use + recruiter-portfolio, at ~$0)

**Well-aligned, no meaningful drift.** Everything built serves one or both locked goals, and the
charter's de-prioritization of startup/defensibility is being respected (no monetization,
sharing-product, or paid-tier work crept in). Two honest watch-items, neither a violation:

- **Personal-use is still demo-shaped.** 10 companies × latest two 10-Ks isn't enough for you to
  actually run your own research on it, and the README's broader data sources (yfinance, FMP, FRED)
  are aspirational — only SEC EDGAR is wired. Closing this is corpus work (plan M6), not a pivot.
- **Watch for breadth-over-depth.** The instinct to add the next feature is strong; the higher-
  leverage move now is to deepen what exists (corpus + eval + the one or two flagship AI features)
  rather than spread thin. The new roadmap is built around that.

---

## The 3 biggest risks right now

1. **The work is done but undemonstrated.** Repo private, likely unpushed, no live URL, no
   screenshots/GIF, `AUTH_SECRET_KEY` a dev placeholder. The single biggest gap between what Mosaic
   *is* and what a recruiter can *see*. Pure upside, low effort.
2. **Trust claims rest on a thin evidence base.** 13 questions / 2 companies; 1.00 scores mean "no
   failures yet," not "robust," and the numbers guard has a known rescaling blind spot. A harder
   question over a wider corpus is where the headline numbers get tested — widen the eval before
   that happens accidentally in front of someone who matters.
3. **Corpus depth caps real personal-use value.** Without more companies, more years, and (per the
   README's own promise) transcripts, "personal use" stays a demo rather than a tool you'd open on
   a Monday to research a real position.

---

## Single highest-leverage next move

**Ship it — make Mosaic publicly demonstrable.** In one focused push: `git push` M4, make the repo
public with a real README (screenshots + a ~30-second GIF of a cited, deep-linked answer), set a
real `AUTH_SECRET_KEY`, and stand up a live $0 demo (Vercel + Neon/Supabase free tier) seeded with
the existing corpus. This converts the strongest part of the project — the build — into the thing
it exists for: a portfolio piece people can see and click. It's mostly packaging and ops, not new
engineering, and it unlocks the career goal immediately. This is Phase 1's finish line; see
ROADMAP **M5 — Ship & Showcase**.

---

## Start / Stop / Change

**Start**
- Treating "shipped and visible" as part of done for Phase 1 — a live URL beats "clone and run."
- Widening the golden eval (≥30 Qs / ≥5–8 companies, including numeric and cross-section) — it's
  both a trust safeguard and a credibility multiplier for the headline numbers.

**Stop**
- Adding new feature *areas* before M5 (ship) and M6 (corpus+eval) land. Depth, then breadth.
- Leaving the dev `AUTH_SECRET_KEY` in place one day longer than the first public/hosted step.

**Change**
- Point the next two months at **deepening the wedge into its best self** (diffs, then a cited
  memo) rather than collecting more surface features. The new roadmap encodes this; the old Phase
  2–4 grab-bag is re-scored there (kept / reordered / cut, each with a reason).

---

## What I verified this session (so the next reader can trust this)

- **Numbers guard** — read `guard.py` end-to-end; confirmed it's called in `answer.py` and returned
  by `routers/ask.py` on both fresh and cached paths. Real, not decorative.
- **RLS** — read migrations 0007–0009 + `app/rls.py` + `tests/test_rls.py`: FORCE on, non-superuser
  role, fail-closed GUC, USING+WITH CHECK, no-pooling-leak + commit-contract tests, 404-not-403 on
  cross-user (no existence leak), covers watchlists AND notes. Genuinely solid.
- **Auth** — argon2, HS256 JWT, httpOnly + SameSite=Lax cookie, Secure gated on env, exp verified,
  fail-closed to 401. Sound.
- **Clean-clone fix** — confirmed by direct read: `requirements.txt` and `.env.example` are now
  complete (the sandbox bash showed a stale copy; host reads are correct).
- **NOT verified in-sandbox (confirm in your terminal):** `pytest` count (claimed 47), the live
  cited-answer click-through, whether M4 is pushed, and whether the repo is public.

---

*Next checkpoint: after M5 (shipped/visible) and M6 (wider corpus+eval). Diff against this file.
— Vera, 2026-06-22*
