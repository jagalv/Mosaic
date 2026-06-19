# Mosaic — Independent Status Assessment

**Author:** Vera (independent strategic & technical advisor)
**Date:** 2026-06-19
**Checkpoint:** End of Milestone 3 — "Ask this filing" (the wedge)
**Basis:** Direct read of the real repo — README, ROADMAP, DECISIONS, WORKLOG, the role
manuals, and the actual code, tests, migrations, and git history in `services/api` and
`apps/web`. Claims spot-checked against source, not summaries.

---

## Overall verdict

**On-track, and genuinely good — with two real holes that are cheap to fix but must be fixed
before anyone calls M3 "done."**

The wedge works. I read the whole grounding path end-to-end — chunking → local bge embeddings →
hybrid RRF retrieval → cite-or-abstain answer → offset-deep-linked citations in the reader — and
it is real, coherent, and well-reasoned, not demo-ware. The engineering judgment on display
(diagnosing IDF-less `ts_rank` as the recall killer, honoring bge query/passage asymmetry, an
eval that *credits abstention on a retrieval miss* instead of gaming the number) is senior-grade.
The $0 constraint is holding. The three-AI + WORKLOG protocol is genuinely working.

What stops me from signing off completely is not the build — it's the **gap between "works on the
dev machine" and "verifiably done."** Two things:

1. **A clean clone cannot start the API.** `requirements.txt` is missing four runtime
   dependencies the code imports (`pgvector`, `sentence-transformers`, `torch`, `google-genai`),
   and `.env.example` omits the M3 env vars. "main is green" is true on exactly one computer.
2. **The trust spine's thinnest point is unguarded.** There is no runtime check that a *number*
   in an answer actually appears in the retrieved excerpts. For the one output Mosaic exists to
   protect, trust currently rests on a prompt, `temperature=0`, and a 10-question eval.

Neither is hard to close. Both matter more than any new feature right now.

---

## Dimension scorecard

### Product & vision — ON-TRACK
The wedge ("Ask this filing," grounded cited Q&A) is the right wedge and the build sequence
served it: infra (M0) → real financials (M1) → filings + section segmentation (M2) → RAG (M3),
each a vertical slice. Nothing premature was built. The differentiator — a footnote `[n]` that
deep-links to the exact source char range in the reader (`reader.tsx`, offset-sliced from the
immutable `content_text`) — is real and is the "oh, that's actually useful" moment the roadmap
promised. *Evidence: `apps/web/.../reader.tsx`, `app/rag/answer.py`, ROADMAP M0–M3.*

### Technical architecture — ON-TRACK
Sound and correctly *under*-engineered for a solo+AI build. One Postgres+pgvector for
relational + vector + full-text; RRF chosen specifically so the cosine and `ts_rank` scales never
need normalizing; real seams that aren't theater (`LLMClient`, `DocumentStore`, the embeddings
module as the single encode path). Deliberate deferrals (R2, SQL view, `services/ingest`) are
documented in DECISIONS with sound reasoning. 384-dim is locked into migration 0004 — an honest,
acknowledged constraint. *Evidence: `app/rag/retrieve.py`, `app/llm/`, DECISIONS 2026-06-18.*

### AI / trust quality — AT-RISK
The scaffolding is excellent — abstain-without-an-LLM-call on empty retrieval, a golden set whose
spans are verified verbatim against real filing text before scoring, multi-span IR-correct recall,
and an eval that distinguishes a retrieval miss from an unfaithful answer. **recall@8 = 1.00 is
real and re-run, not projected.** I am scoring this AT-RISK *despite* the quality, for three
reasons: (a) **no runtime numbers guard** — nothing programmatic stops a fabricated figure; the
only `.isdigit()` in the RAG path is citation parsing. (b) The evidence base is thin: 13 questions,
heavily single-company (7 AAPL / 3 MSFT), with **2 of 3 abstention checks still unconfirmed**
(quota-blocked). (c) recall@8 = 1.00 over 10 questions should read as "no failures observed yet,"
not "solved." The spine is well-built but lightly tested for something this load-bearing.
*Evidence: `app/rag/answer.py`, `app/eval/run_eval.py`, `tests/golden_qa.json`, WORKLOG 06-19.*

### Execution & velocity — ON-TRACK
M0 → M3 inside roughly two calendar days (WORKLOG timestamps), with clean handoffs and visible
discipline: Alexander diagnosed weak recall, **probe-validated the fix read-only, and stopped at
the eval gate rather than tuning blindly.** That is exactly the behavior you want and rarely get.
The WORKLOG-as-shared-memory protocol is doing its job. *Evidence: WORKLOG 06-18/06-19 entries.*

### Cost & operations — ON-TRACK
$0 is holding honestly: local bge embeddings (no API cost, no rate limit on bulk ingest), Gemini
free tier, local Postgres, free SEC EDGAR. No paid service appears anywhere in `.env.example`.
The one real operational fact: the Gemini free tier (~20 req/day/model) is genuinely constraining
— it is *why* M3 isn't 100% closed, and it makes `answer_cache` load-bearing rather than a nicety.
Fine for personal use; a throttle for any live-Q&A demo. *Evidence: `.env.example`, `app/llm/gemini.py`, DECISIONS 06-19.*

### Risk & defensibility — AT-RISK (inherent, not a regression)
The investor critique stands. The moat is thin: RAG-over-public-filings is reproducible by anyone,
and the data is free/public (great for $0, weak for defensibility). Single-LLM-provider dependency
is seam-mitigated but still a single point. The corpus is 10 companies × latest two 10-Ks — right
for a wedge, not a product. None of this is a reason to stop; it is the honest ceiling on the
"this could be a company" goal. The sharper, harder-to-copy asset is the *persistent research
workspace* (memos, notes, theses as first-class objects) — that, not the RAG, is where a real moat
could live. *Evidence: README "What makes it different," ROADMAP Phase 2.*

### Career value — ON-TRACK (high ceiling, packaging gap)
The work is genuinely recruiter-impressive: real RAG with honest evals, an articulated trust
contract, IR-literate retrieval reasoning, a clean full-stack vertical slice, and a DECISIONS log
that by itself signals senior judgment. But **a recruiter cannot currently clone and run it**
(the reproducibility hole), there are no screenshots/GIF/demo, and the repo is still private. The
work is A-grade; the packaging is C-grade. Closing that is the cheapest, highest-leverage career
move available. *Evidence: DECISIONS.md, ROADMAP "Make it presentable" (all unchecked), repo state.*

---

## The 3 biggest risks right now

1. **The reproducibility hole quietly invalidates "done."** `app/models.py:12` imports
   `pgvector.sqlalchemy` at module top — so the ORM, and therefore the entire API, fails to import
   on a fresh `pip install -r requirements.txt`. `torch`, `sentence-transformers`, and
   `google-genai` are also imported but unpinned, and `.env.example` is missing `GEMINI_API_KEY`,
   `LLM_MODEL`, and `EMBEDDING_MODEL`. This contradicts what the WORKLOG records as done, and it
   silently breaks the README, the next AI's onboarding, and any recruiter clone. Cheapest fix
   here, highest blast radius if left.

2. **The trust spine has no numbers guard, and a thin eval base.** Mosaic exists because "generic
   AI hallucinates on filings." Today that promise is defended by a prompt + `temperature=0` + ~10
   verified questions — not a guarantee. One confidently wrong number in a demo undoes the entire
   thesis. The fix is small (flag any answer-number absent from the retrieved excerpts; expand the
   golden set to include numeric questions across more companies).

3. **The working tree is not clean, and the sandbox git view is alarming.** Sandbox `git status`
   shows *staged deletions of every core source file* (`models.py`, `main.py`, `rag/*`,
   `routers/*`, `llm/*`) — almost certainly index lag (the files are present and correct on disk),
   **but you must confirm this in your own terminal before committing — committing that state would
   delete the codebase.** Separately, there is a real pile of uncommitted modifications
   (`config.py`, `reader.tsx`, `run_eval.py`, `edgar.py`, `.env.example`, `ONBOARDING.md`) beyond
   the last commit: M3 is "committed" but the tree is not in a clean, known-good state.

---

## Single highest-leverage next move

**Close the gap between "works on my machine" and "verifiably done," in one short session — do not
start anything new until it's done.** Concretely: pin the four missing deps (with the CPU-only
`torch` index URL), add the missing vars to `.env.example`, verify a *clean clone* boots the API,
run the final two abstention checks when the Gemini quota resets, eyeball one live cited-answer
click-through, and commit a clean tree. That single session converts "~95%, works locally" into
"done and shareable," which simultaneously unblocks the trust claim's credibility, the career value,
and the next Sally's onboarding. It is cheap and it unlocks everything downstream.

---

## Start / Stop / Change

**Start**
- A runtime numbers-faithfulness check — even a cheap one: if a number in the answer is not found
  in any retrieved excerpt, force an abstain or flag it. Guard the spine in code, not just prompt.
- Expanding the golden set to ≥30 questions across ≥5 companies, including numeric questions.
- Packaging for the audience that matters: screenshots + a short GIF, then make the repo public —
  but only *after* the clean-clone fix, or the first impression is a stack trace.

**Stop**
- Calling milestones "done/green" on dev-machine-only verification. "Done" must mean "a clean clone
  runs it." Logging is already part of your definition of done; extend it to reproducibility.
- Adding companies, filings, or new features until M3 is verifiably closed and committed clean.

**Change**
- Fold reproducibility + a clean committed tree into the Definition of Done (see ROADMAP).
- Soften the "startup" goal language to **portfolio + personal-use first, startup-optional** until
  there's a sharper moat — *or* pick one defensibility angle (the persistent research-workspace /
  memo layer is the candidate; it's harder to copy than RAG) and aim Phase 2 squarely at it. This
  is a strategic call and it's yours — I'm flagging it, not making it.

---

## What I verified (so the next reader can trust this)

- **recall@8 = 1.00** claim — consistent with `run_eval.py` logic and the multi-span `golden_qa.json`;
  the methodology is honest (verbatim span check, abstention credited on miss). Not independently
  re-run in-sandbox (no DB/deps here) — *James, confirm with `python -m app.eval.run_eval` in your
  terminal.*
- **25/25 pytest** — 25 test functions exist (`test_chunking` 7, `test_filing_sections` 5,
  `test_golden_financials` 4, `test_golden_qa_set` 3, `test_grounding` 6). `test_grounding` uses an
  injected fake LLM (offline, good). Counts match the claim; a live run needs your terminal.
- **Grounding contract** — enforced in `answer.py` (answer-only-from-excerpts prompt, exact-string
  abstention, abstain-without-LLM on empty retrieval, grouped-citation parsing). Confirmed in code.
- **$0 constraint** — no paid service in `.env.example`; embeddings local; LLM on free tier. Holds.
- **The two holes above** — confirmed directly: `requirements.txt` (6 deps, none of the M3 four),
  `models.py:12` top-level pgvector import, `.env.example` (no LLM/embedding vars), and no numeric
  runtime guard in `app/rag/`.

---

*Next checkpoint: re-run this assessment after M3 is committed clean and M4 (persistence + RLS)
lands. Diff against this file. — Vera, 2026-06-19*
