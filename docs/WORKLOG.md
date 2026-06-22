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

### 2026-06-19 — Sally (Opus) — team transition + Vera end-of-Phase-1 review prepped
**Prompted to:** Prep a fresh-Alexander chat transition + ready a neutral 3rd-party review for next session.
**Did:** M4 complete (prior entry). Wrote a transition/kickoff prompt for a NEW Alexander chat (orient via
ALEXANDER.md + CLAUDE.md + latest WORKLOG/ROADMAP/DECISIONS; NO active build — await direction after the
review). Reusing **Vera** (not a new persona) for the end-of-Phase-1 review; tweaked VERA.md to
de-prioritize the stale "startup" goal per DECISIONS 2026-06-18 (portfolio + personal use first). Wrote
Vera's review kickoff prompt: audit the real repo (esp. M4 RLS/auth + the wedge), score dimensions +
diff against the M3 STATUS.md, judge Phase-1-v1 readiness, and write the revised forward roadmap + update
STATUS.md.
**Verified:** Docs only.
**Next / handoff:** James starts next session with the Vera review (kickoff handed). Standing: commit
M4a–d + the polish pass from his terminal; run pytest + a live click-through; Bobby sets a real
AUTH_SECRET_KEY. Phase-1 remainder = the "Make it presentable" block.
**Roadmap:** No change (M4 closed in the prior entry).

---

### 2026-06-19 — Sally (Opus) — M4d Session 2b verified — ★ MILESTONE 4 COMPLETE
**Prompted to:** Verify M4d-2b (notes UI) and close out Milestone 4.
**Did (Alexander, M4d-2b):** Notes UI — `NotesPanel` (reusable per-target: company ticker / filing
accession; anonymous → "Log in to add notes" with NO fetch; authed → create/list + per-note inline
edit/delete), placed on the company page + filing reader; `NotesManager` (the /notes index grouping all
notes by company/filing with links + edit/delete); /notes page self-guards (getMe→null→/login?next=/notes)
then server-fetches. client-api +notes CRUD; server-api +getNotes; lib/api +Note/NoteTarget; Notes nav
no longer "Soon". Removed the now-unused proxy.ts.
**Verified (Sally, real files):** /notes self-guards before any fetch ✓; NotesPanel effect is gated on
`authed` so anonymous users get the login prompt and NO 401 fetch ✓; proxy.ts + middleware.ts both gone
✓; NotesPanel wired into company page + reader ✓. `next build` reported clean (11 routes). Backend
untouched.
**Next / handoff:** ★ M4 is DONE end-to-end — auth + watchlists + notes + DB-enforced Postgres RLS +
cross-user security test + full UI, with public browse and a gated personal workspace. James, final
checklist (your terminal, no AI usage): (1) `docker compose up` + `pytest` (the RLS security test needs
Postgres) → expect green; (2) `npm run dev:web` and click through once logged-in AND logged-out — the
UI has only been verified by `next build` + flow tracing, so it deserves real eyes before you call it
demo-ready; (3) commit the whole M4 chain (M4a–M4d) + the earlier polish pass; (4) have Bobby set a real
AUTH_SECRET_KEY in `.env`. After that, the only Phase-1 work left is "Make it presentable" (public repo,
README screenshots/GIF).
**Roadmap:** ★ Milestone 4 COMPLETE (backend + UI). M0 deferred-auth box closed (login/signup UI live).
Remaining Phase 1: the "Make it presentable" block.

---

### 2026-06-19 — Sally (Opus) — M4d Session 2a verified (public-browse refactor + watchlist UI)
**Prompted to:** Verify M4d-2a + docs.
**Did (Alexander, M4d-2a):** Guard refactor for PUBLIC BROWSE — (app)/layout.tsx no longer redirects;
calls getMe() and passes user|null to an auth-aware AppShell. /watchlist self-guards
(getMe→null→redirect /login?next=/watchlist) then server-fetches getWatchlists (cookie-forwarded).
Watchlist UI: WatchlistManager (create/delete list, remove item, re-fetch), company-header WatchButton
(authed → popover of lists + "New list" with added-state; anonymous → /login?next=). client-api +5
watchlist calls (credentials:include); server-api +getWatchlists; lib/api +Watchlist/WatchlistItem
types; topbar auth-aware (chip+logout | "Log in"); nav Watchlist no longer "Soon".
**Verified (Sally, real files):** Read (app)/layout.tsx (redirect REMOVED; user|null → shell = public
browse ✓) and /watchlist/page.tsx (self-guards BEFORE any data fetch → clean redirect, no 401 page ✓).
`next build` reported clean (11 routes). Backend untouched. Access model correct: browse public,
personal page gated, data fetched only post-guard.
**Next / handoff:** Session 2b (LAST M4 slice) = notes UI — prompt handed to James. notes GET already
returns target labels (ticker/name/accession) so no backend change needed. Minor cleanup: proxy.ts is
now unused (layout doesn't redirect; routes use fixed/client-side next) — drop it in 2b. James: commit
M4d-2a from your terminal.
**Roadmap:** M4 UI — auth foundation + watchlist UI done; notes UI = 2b, then M4 complete.

---

### 2026-06-19 — Sally (Opus) — M4d Session 1 verified (auth foundation UI)
**Prompted to:** Verify Alexander's M4d-1 (frontend auth foundation) + docs.
**Did (Alexander, M4d-1):** Client/server API split — `lib/client-api.ts` (browser,
`credentials:include`: signup/login/logout/me), `lib/server-api.ts` (`getMe()` forwards the request
cookie via next/headers), `lib/api.ts` (+`AuthUser` type only; public fetches untouched). Auth UI:
`/login` + `/signup` (public, outside `(app)`), shared auth-form, `AuthProvider` (client context
seeded server-side + logout). Server guard in `(app)/layout.tsx` (`getMe()` → 401 redirect
`/login?next=`). `proxy.ts` stamps `x-pathname` for `?next` (Next 16 renamed middleware→proxy).
Topbar real user chip + logout; hero "Log in" link.
**Verified (Sally, real files):** Read server-api.ts (correct cookie-forward; null on 401/unreachable)
+ (app)/layout.tsx (server guard correct). Grep confirms server-api is imported ONLY by the server
layout, so the omitted `server-only` directive (no-deps lock) is safe — no client bundle pulls
next/headers. `next build` reported clean (not re-run here). Backend untouched.
**Next / handoff:** TWO Session-2 decisions pending James (asked): (1) public-browse vs gated —
company/filing/dashboard currently sit inside the guarded `(app)` group so they require login; recommend
making browse/read/ask PUBLIC (recruiter sees the wedge without signup) + guard only the personal layer;
(2) the #4 Watch-UX pick. Session 2 = watchlist + notes UI (+ guard-scope refactor if public). James:
commit M4d-1 from your terminal.
**Roadmap:** M4 UI in progress — auth foundation done; workspace UI + guard scope = Session 2.

---

### 2026-06-19 — Sally (Opus) — M4c verified (notes + RLS)
**Prompted to:** Verify M4c (notes) before the final UI slice.
**Did (Alexander, M4c):** `notes` table (migration 0009, chain 0008→0009): user_id FK→users CASCADE,
body, created_at/updated_at (onupdate-bumped), two nullable targets `company_cik`→companies.cik and
`filing_id`→filings.id with a CHECK that exactly one is set; RLS ENABLED + FORCED + fail-closed
`notes_owner` policy (mosaic_app CRUD via 0008's default privileges — no GRANT). `routers/notes.py`:
POST (exactly-one target; ticker/accession resolved), GET (`?company=`/`?accession=` filters), PATCH
(bumps updated_at), DELETE — all via get_rls_session, flush-not-commit, not-yours→404. Wired in main.py.
**Verified (Sally, real files):** Read migration 0009 — notes has its OWN ENABLE+FORCE RLS + fail-closed
policy (the per-table trap handled), CHECK exactly-one-target correct, sequential 0008→0009. test_rls.py
genuinely extended: notes DB-level (invisible/un-writable to B; empty GUC→0 rows) + API-level (B's GET
excludes, PATCH/DELETE→404; A owns CRUD; 422 on neither/both targets). Reported 47 passing w/
APP_DATABASE_URL; 42 + 5 skipped offline. NOT re-run here (no sandbox Postgres) — confirm green in your
terminal.
**Next / handoff:** James: run pytest + commit M4c (with M4a/M4b) from your terminal. Only M4d left —
the frontend: login/signup, auth state, protected routes, wiring watchlist + notes into the existing
shell stubs (design system already in place). Sally to write the M4d prompt next.
**Roadmap:** M4 — notes done; watchlists/RLS/security-test already done. M4 BACKEND COMPLETE; M4d (UI)
is the last slice.

---

### 2026-06-19 — Sally (Opus) — M4b verified (RLS + watchlists, incl. superuser-bypass fix)
**Prompted to:** Confirm M4b is genuinely done before starting M4c (which reuses the RLS pattern).
**Did (Alexander, M4b + fix):** `watchlists` + `watchlist_items` (migration 0007) with RLS
ENABLED + FORCED + policies on `current_setting('app.current_user_id')`; `get_rls_session` dep
(`set_config(...,is_local=>true)`, sole committer); 5 watchlist endpoints; cross-user security test.
Superuser-bypass fix (migration 0008): dedicated `mosaic_app` role (NOSUPERUSER NOBYPASSRLS) + coarse
CRUD grants + ALTER DEFAULT PRIVILEGES (auto-covers M4c `notes`); db.py engine split (admin
DATABASE_URL for alembic/ingestion/eval; APP_DATABASE_URL/`mosaic_app` for EVERY API request, no
fallback); rls.py + `get_session` on the app engine. config + .env.example wired (APP_DATABASE_URL).
**Verified (Sally, real files):** Read migration 0008 (role NOSUPERUSER NOBYPASSRLS ✓; grants +
default privileges ✓), db.py (app engine, no silent admin fallback ✓), rls.py (AppSessionLocal +
set_config is_local + sole-committer ✓), test_rls.py — it connects AS `mosaic_app` via `app_engine()`
and proves DB isolation, fail-closed empty GUC, no pooling leak, API cross-user 404s, and the
multi-statement commit-contract. Because it exercises the non-superuser role, it genuinely proves
isolation. NOT re-run here (sandbox has no reachable Postgres+role) — **James to confirm green via
`docker compose up` + pytest before committing.**
**Next / handoff:** James: run pytest + commit M4a & M4b from your own terminal (sandbox git lag).
M4c (notes) reuses this exact RLS pattern and the default privileges already cover its table. M4d = UI.
**Roadmap:** M4 — watchlists + RLS + cross-user security test done (backend); notes = M4c; UI = M4d.

---

### 2026-06-19 — Sally (Opus) — M4a verified + logged
**Prompted to:** Verify Alexander's M4a auth-backend build + handle the docs close-out (role split:
Sally owns docs/checks).
**Did (Alexander, M4a):** Auth backend — `users` table (migration 0006, chain 0005→0006);
`app/auth.py` (argon2 hash/verify; HS256 JWT with `sub` + 7-day `exp`; `mosaic_session` httpOnly /
SameSite=Lax cookie, `Secure` gated by `AUTH_COOKIE_SECURE`; `get_current_user` = the RLS seam);
`app/routers/auth.py` (signup/login/logout/me). Wired `auth.router` in main.py; config +=
`auth_secret_key`/`auth_cookie_secure`; requirements += `argon2-cffi==23.1.0`, `PyJWT==2.10.1`;
`.env.example` += `AUTH_SECRET_KEY`/`AUTH_COOKIE_SECURE`. 9 offline auth tests. All 4 review
refinements folded in (JWT exp+verify; identical-401 no-enumeration; logout clears matching attrs;
min-8 password).
**Verified (Sally, on real files):** Read `auth.py` + `routers/auth.py` — security logic correct
(expiry verified by `jwt.decode`; no-enumeration login; cookie attrs match on clear). Migration 0006
`down_revision=0005`. `requirements.txt` + `.env.example` confirmed via Read (bash showed them empty
= mount-lag on the phantom-deleted files; Read is authoritative). Did NOT re-run pytest (sandbox
can't); Alexander reported 42 passing (33+9), consistent with imports + static review. No frontend
touched.
**Next / handoff:** James commits M4a from his OWN terminal first (sandbox git lag = phantom
deletions; do NOT `git add -A`). Suggested: `feat: m4a — auth backend (users + argon2 + JWT cookie
sessions, get_current_user)`. Set a real `AUTH_SECRET_KEY` in `.env` (Bobby — example default is
`dev-insecure-change-me`). Then M4b — RLS mechanism + watchlists: `SET LOCAL app.current_user_id`
inside the request txn (compose `get_current_user` + `get_session`), RLS policies, and the cross-user
security test. Sally to write the M4b prompt next.
**Roadmap:** M0 deferred-auth item annotated (backend done M4a; UI in M4d). No M4 milestone boxes yet
(watchlists/notes/RLS = M4b/c).

---

### 2026-06-19 — Sally (Opus) — role-split note
**Prompted to:** Record a working agreement to save Alexander's usage.
**Did:** Updated `SALLY.md §1` — Alexander remains lead on all main development (most capable model
/ lead engineer; don't overstep). Sally now absorbs the cheap ancillary work that burns his tokens:
doc updates, WORKLOG/ROADMAP/DECISIONS close-outs, light verification/spot-checks, tidying. Rule of
thumb: code/architecture = Alexander; docs/checks = Sally.
**Verified:** Doc change only.
**Next / handoff:** Bobby/Alexander — heads up, Sally will handle close-out paperwork & light checks
going forward so your sessions stay focused on code/IT.
**Roadmap:** No change.

---

### 2026-06-19 — Sally (Opus) — M4 Session-1 close-out finished
**Prompted to:** Finish Alexander's polish-pass close-out (he was cut on usage mid-step-2). James
is happy with the look — no design changes.
**Did:** Alexander completed Step 1 — the design-system DECISIONS entry. I finished the remaining
close-out myself (file edits only, to spare Claude-Code usage): this WORKLOG entry + a ROADMAP note
ticking the design-system + polish pass under "End of Phase 1 — Make it presentable." No code changed.
**Verified:** DECISIONS token values match `globals.css` exactly (teal primary `0.72 0.12 190` dark /
`0.58 0.13 195` light; violet highlight `0.5 0.13 295` dark; layered surfaces 0.165/0.185/0.205;
hairline borders). Trust spine already confirmed static-identical (prior entry). Runtime smoke test
only PARTIAL: Alexander confirmed the styled 404 path works (accidentally routed a query into the
topbar ticker-search → landed on the new not-found page) but did NOT finish the footnote-highlight /
grouped-citation / amber-banner / abstention click-through before being cut. Regression risk low —
reader logic is byte-identical to the working M3 reader.
**Next / handoff:** Two items need James's OWN terminal (zero AI usage): re-run `next build` and
`pytest` to reconfirm green, and a ~30-sec click-test of one cited answer in the reader (footnote →
exact highlight + scroll; amber banner on an unsupported figure). Then James commits from his terminal
— sandbox git shows phantom deletions (lag); do NOT `git add -A` there. Suggested message:
`feat: design-system + visual polish pass (teal/dark, app shell, states)`. After commit the polish
phase is DONE. Session 2 = M4 features (auth/RLS/watchlists/notes) — STILL needs James's auth/RLS
stack decision before I write that prompt.
**Roadmap:** Design-system + polish pass marked done under "Make it presentable." No M4 boxes ticked.

---

### 2026-06-19 — Sally (Opus) — verification of Alexander's M4 Session-1 polish build
**Prompted to:** Verify Alexander's M4 Session-1 polish build (he used ~90% of James's usage and
was cut short at the screenshot step, before logging close-out).
**Did (Alexander, this session):** Built the design-system + polish pass A–F. globals.css token
rewrite (teal primary hue ~190/195, cool-neutral base hue 248, added success/warning + a violet
highlight token, both modes), **fixed the self-referential `--font-sans` bug**, added `.tnum`
tabular helper + heading tracking. Inline blocking theme script in root layout (default dark,
persists, no OS-follow, no flash). Custom app shell (sidebar/topbar/theme-toggle/ticker-search/
mobile) via an `(app)` route group — **URLs unchanged**, old routes removed. Reusable primitives
(page/section headers, MetricCard, Delta, Chip, CitationChip, Empty/Error states); added only
`skeleton` + `tooltip` (free). Restyled hero `/`, dashboard/companies grid, company page (metric
cards + deltas + tabular tables), filing reader, settings (health check moved here); added
loading/error/404 states. Found + fixed a real runtime bug: `<Button render={<Link/>}>` needed
base-ui `nativeButton={false}` (was hanging the renderer) — applied in all 3 spots.
**Verified (Sally, on the real files):** **Trust spine INTACT** — `reader.tsx` `bodyStart`/
`renderBody` offset math byte-identical to pre-change, grouped-citation split `/(\[[\d,\s]+\])/g`
unchanged, `scrollIntoView` effect unchanged, numbers-guard banner preserved (now on `--warning`),
abstention preserved (cleaner). Violet highlight (hue ~295/300) distinct from teal/amber/green/red
per guardrail. Font bug fixed; theme script + dark default correct; route group on disk; Button fix
in all 3 places. Citation external-link → `primary_doc_url` is REAL end-to-end (models.py:61 /
filing.py:46). Alexander did NOT commit (log ends at a0458fc) — correct. **NOT independently
re-run:** `next build` / `pytest` (sandbox would give false results — Windows node_modules + lagging
git); relied on his clean-build claim + static review. **NOT done: screenshots** — preview_screenshot
broke and no Chrome ext, so the VISUAL sign-off (James's top priority) is the one open item.
**Next / handoff:** (1) Eyes-on: run `npm run dev:web` and review every screen in dark + light (or
I can capture via Chrome/computer-use once the 3 services are up). (2) After sign-off, James commits
from his OWN terminal — sandbox git shows phantom deletions = lag; do NOT `git add -A` from it.
(3) Write the design-system DECISIONS entry once token values are visually confirmed (deferred in
case James tweaks). (4) Then Session 2 = M4 features — still needs James's auth/RLS decision.
**Roadmap:** No code milestone ticked. Polish pass maps to "End of Phase 1 — Make it presentable"
(screenshots/GIF still pending). No M4 boxes.

---

### 2026-06-19 — Sally (Opus)
**Prompted to:** Kick off Milestone 4 strongly; James wants the site to look phenomenal /
interview-grade (polish ~ as important as features for demoing his work).
**Did:** Set the sequencing with James — **POLISH FIRST** (Session 1 = design system + visual
polish, zero features), then **M4 features** (Session 2). Locked the visual direction:
Linear/Vercel-grade modern fintech, **TEAL** accent, **dark-mode-first** (both modes proper),
tabular numerals on all financials, app shell with sidebar; mocked it for James — approved.
Wrote Alexander's Session 1 prompt (design-system + polish pass) in house style:
ORIENT→PLAN-ONLY-THEN-STOP, locked choices vs surfaced decisions (token values / landing /
theme persistence), named the hard part — a token-driven SYSTEM (not a paint job) **and a
do-not-regress contract on reader.tsx's trust-spine UI** (citation deep-link + exact char-offset
highlight + numbers-guard amber banner + abstention). DoD includes both-mode screenshots,
`pytest` still green (backend untouched), no new paid deps; don't auto-commit.
**Verified:** Read the real frontend before prompting — Tailwind v4 + shadcn oklch tokens
(both modes, sidebar tokens predefined), Geist/Geist Mono via next/font ($0), lucide-react
already in deps → it's a re-theme + shell pass, not a rebuild. Confirmed M0–M3 committed clean
via `git log` (f5126ef + a0458fc); the sandbox's phantom staged-deletions are the known
mount-lag, not real — did not alarm James.
**Next / handoff:** James approves/tweaks Alexander's Session 1 plan when posted (I review with
him). **Session 2 = M4 features still NEEDS James's auth/RLS stack decision** before I write that
prompt — options on the table: local-first real Postgres RLS (my lean: $0, clone-runnable,
DB-enforced) vs Supabase vs Clerk. Do NOT tick M4 boxes for the polish pass.
**Roadmap:** No code yet. Polish pass maps to "End of Phase 1 — Make it presentable"; M4 boxes
untouched.

---

### 2026-06-19 — Sally (Opus) — RETIRING / HANDOFF
**Prompted to:** Hand the lead role to a new Sally and ensure a clean, high-bar onboarding.
**Did:** Milestones 0–3 are complete, committed, and pushed (the wedge works: grounded, cited,
numbers-guarded Q&A over real filings). Updated `docs/SALLY.md` — first task is now the **Milestone 4**
prompt (research workspace + auth/RLS, with a cross-user security test as the must-be-correct core),
and added a "raise the bar" section of hardest-won lessons. Recorded the project objective (personal
portfolio + personal use, NOT startup) in DECISIONS. Created Vera's advisor charter (`docs/VERA.md`);
her audit is in `docs/STATUS.md` and the reset roadmap.
**Verified:** Confirmed M3 done against real files (guard.py, migration 0005 sequential, 33 tests);
caught that Vera's "deps missing / clean clone can't boot" was a sandbox mount-lag stale read — deps
were already pinned; Alexander then proved a clean-clone boot.
**Next / handoff:** New Sally: read `docs/SALLY.md` first (esp. §6.5 first task + the raise-the-bar
section), then `docs/STATUS.md` + `docs/ROADMAP.md`, and write Alexander's Milestone 4 prompt. Team
unchanged: Alexander (engineer), Bobby (IT), Vera (advisor, on call). Onboarding header in
`docs/ONBOARDING.md`.
**Roadmap:** No code change. M0–M3 done; M4 (auth/RLS workspace) is next, the long pole of Phase 1.

---

### 2026-06-19 — Alexander (Claude Code)
**Prompted to:** Final M3 close-out — run the quota-gated checks (full faithfulness eval + live UI/citation/guard check) and, if they pass, mark Milestone 3 DONE.
**Did:**
- Ran `python -m app.eval.run_eval --llm` on **gemini-2.5-flash-lite** (daily quota had reset). Completed full set.
- Live check via the `/ask` endpoint + `content_text` slicing (the exact path the reader renders): asked AAPL FY2025 a net-sales question, resolved each citation's char range to its source span, inspected the numbers-guard result.
- Ticked the remaining M3 ROADMAP boxes (faithfulness, close-out 2 abstentions + live check) and marked **Milestone 3 DONE**. No new DECISIONS entry — no new architectural choice this session (verification only), per "one entry per genuine decision."
**Verified:** **Faithfulness = 13/13 = 1.00** — 10/10 answerable answered with real citations (recall_hit on all); **3/3 unanswerable abstained**, including the previously-pending `appstore-dau` and `msft-cfo-salary`. recall@8 = 1.00. Live: answer "$416,161M (FY2025) / $391,035M (FY2024)" cited [1,5,6,7] → those char ranges land on the segment table (components sum to 416,161) and the income-statement header; **numbers guard returned [] (no false-fire on the correct figures)**. `pytest` 33/33 green; no code changed this session.
**Next / handoff:** **M3 is DONE.** Only open item is James's **clean commit** — confirm `git status` in a real terminal first (sandbox shows phantom deletions = lag). After that, M4 (persistence: watchlists/notes + auth/RLS + cross-user security test) is next, and it's the long pole (see Vera's STATUS.md / ROADMAP estimates). Suggested commit: `feat: m3 numbers guard + clean-clone docs; close out M3 (faithfulness 13/13, recall 1.00)`.
**Roadmap:** Milestone 3 — all boxes ticked; **marked DONE**. Close-out block: everything done except the clean commit (James).

---

### 2026-06-19 — Alexander (Claude Code)
**Prompted to:** M3 close-out — (1) build a runtime numbers guard (PLAN-first), (2) prove a clean-clone boot, (3) finish the 2 abstention evals + a live click-through. Goal is now personal portfolio + personal use. Don't "fix" the deps/env (Vera read stale copies).
**Did:**
- **Verified Vera's two "holes" were stale reads** — `requirements.txt` already pins pgvector/sentence-transformers/google-genai (torch = documented CPU pre-step), `.env.example` already has the 4 M3 vars. Changed nothing there.
- **Task 1 — Numbers guard (approved plan, flag+warn):** new `app/rag/guard.py` (digit-core matching: drops `$`/commas/`%`/decimals/scale-words, substring-tests answer figures vs retrieved-text figures; **≥4-digit** scope to avoid spurious small-number collisions). Wired into `answer_question` → `AnswerResult.unsupported_numbers`; surfaced in `/ask` response, persisted to `answer_cache` + `ai_interactions` (migration `0005`), and shown as an amber warning banner in `reader.tsx`. 8 new tests (supported / fabricated / formatting / threshold / year / citation-not-a-number / 2 integration). Known limit documented: a *re-scaled* figure ("383.3 billion" from "383,285 million") won't match — exactly why policy is flag-and-warn, not withhold.
- **Task 2 — Clean-clone boot:** built a fresh venv, ran the documented install (CPU torch first → `pip install -r requirements.txt`), confirmed torch stayed `+cpu` (no CUDA pull), API imports (9 routes), **pytest 33/33 on the clean venv**, and a full end-to-end mock answer with a real deep-link range. Smoothed the README "Running locally" (CPU-torch-first step, `chunk`+`embed` ingest steps, GEMINI_API_KEY/mock note) — no unpinning.
- **Task 3 — partially blocked:** the clean venv reached Gemini correctly (got a 429, i.e. SDK/key/request all work) but the **per-day free-tier cap (20/model) on gemini-2.5-flash-lite is still exhausted today** — the 2 abstention checks + live cited click-through can't run until it resets.
**Verified:** `pytest` 33/33 (dev venv **and** clean venv); `next build` clean; guard end-to-end via mock (response field + cache column persist); clean-venv boot proven. Numbers guard: fabricated `$999,999` flagged, `$383,285 million` vs `383,285` supported.
**Next / handoff:** **Only quota-blocked items remain to fully close M3** (not code): when gemini-2.5-flash-lite's daily quota resets, run `python -m app.eval.run_eval --llm` (confirm `appstore-dau` + `msft-cfo-salary` abstain) and click one cited answer in the reader to confirm the footnote highlights truly-supporting text. Or use a sibling model with fresh daily quota (e.g. gemini-3.5-flash) if you want it done today — note the model. `main` green. Did NOT commit; **confirm `git status` in your own terminal first** (sandbox shows phantom deletions — lag). Suggested commit: `feat: m3 numbers guard (flag-and-warn) + clean-clone install docs`.
**Roadmap:** M3 — added runtime numbers guard; close-out block: deps/env verified-already-correct, clean-clone boot ✓; 2 abstentions + live click-through + clean commit still open (quota/James).

---

### 2026-06-19 — Vera (independent advisor, Opus)
**Prompted to:** Checkpoint review at M3 (the wedge): audit the real repo, score each charter
dimension, name the top risks + highest-leverage move, reset ROADMAP, and write a durable STATUS.
**Did:**
- Read the real code/tests/migrations/git across `services/api` + `apps/web`, not summaries.
  Verdict: **on-track and genuinely good**, with two cheap-but-mandatory holes before M3 is "done."
- **Found: clean-clone reproducibility hole.** `requirements.txt` is missing 4 imported runtime
  deps (`pgvector`, `sentence-transformers`, `torch`, `google-genai`); `models.py:12` imports
  pgvector at module load, so a fresh `pip install` can't even start the API. `.env.example` is
  missing `GEMINI_API_KEY`/`LLM_MODEL`/`EMBEDDING_MODEL`. Contradicts what was logged as done.
- **Found: trust-spine numbers gap.** No runtime check that a number in an answer appears in the
  retrieved excerpts; faithfulness proven on ~10 Qs / 2 companies with 2 abstentions still pending.
- Wrote `docs/STATUS.md` (dated, scored, evidence-cited) and reset `docs/ROADMAP.md` (added a
  Definition of Complete, a "Close-out M3" block, and honest AI-assisted-solo estimates).
**Verified:** Confirmed in source — `requirements.txt`, `models.py:12`, `.env.example`, no numeric
guard in `app/rag/`. recall@8=1.00 and 25/25 pytest are consistent with the code but NOT re-run
in-sandbox (no DB/deps) — James to confirm in his terminal. **Caution:** sandbox `git status`
showed phantom staged deletions of all core files (files are present/correct on disk — index lag);
confirm `git status` in your own terminal before committing.
**Next / handoff:** Highest-leverage move = one session to close the clean-clone gap + the 2
abstention checks + a clean commit, before starting anything new. Then M3 is truly done and the
repo is shareable. Full Start/Stop/Change in STATUS.md. Did NOT commit (per protocol — James commits).
**Roadmap:** No checkboxes changed. Added Vera reset section + "Close-out M3" block + Definition of
Complete; M3 stays ~95% until the close-out items land.

---

### 2026-06-19 — Alexander (Claude Code)
**Prompted to:** Close M3: (1) apply OR-based keyword fix in `app/rag/retrieve.py`, re-run eval, report ACTUAL recall (≥0.9); (2) run faithfulness with the GEMINI_API_KEY. Stop + report if recall still weak after the fix.
**Did:**
- **Keyword fix (retrieve.py):** `_keyword_terms()` lowercases/tokenizes/drops stopwords + OR-joins into `to_tsquery` (was AND `websearch_to_tsquery`). Added `_company_stop_tokens()` — in single-filing search the filing's own company name is in nearly every chunk, and Postgres `ts_rank` has no IDF, so the name + common terms drown the answer chunk; dropping the company name is what actually moved recall. Semantic path untouched.
- **Eval methodology fix (golden_qa.json):** inspecting the 2 stubborn misses showed retrieval was surfacing genuinely-correct passages at rank 1–2 — my single-exact-span answer key was too strict (e.g. the income-tax note for "effective tax rate"; the other clause of the same R&D sentence). Broadened those 2 questions to the multiple legitimate answer spans (standard IR practice; spans verified verbatim in the filing).
- **Citation-parser bug (answer.py + reader.tsx):** the model emits grouped citations like `[1, 2]`; the regex only matched `[1]`, silently dropping them (answers looked uncited; UI got no deep-link). Fixed both backend extraction and frontend rendering to parse grouped brackets.
- **Gemini model/availability:** configured `gemini-2.0-flash` returns `429 limit:0` on this key (not served). Listed the key's models — it's the 2.5/3.x lineup. Switched default → **gemini-2.5-flash-lite** (verified end-to-end). Added bounded 429-retry to GeminiClient that honors the server retry delay but fails fast on per-DAY caps.
**Verified:** **recall@8 = 1.00 (10/10)** — actual, re-run, not projected. `pytest` 25/25 green; `next build` clean. **Faithfulness (gemini-2.5-flash-lite): 10/10 answerable answered WITH grounded citations to supporting chunks (0 hallucinations observed); 1/3 unanswerable confirmed abstaining** (`india-market-share`, twice). The grouped-citation fix flipped 2 false "uncited" results to correct. **2/3 unanswerable (`appstore-dau`, `msft-cfo-salary`) NOT verified — the free tier is ~20 req/day/model and my eval runs exhausted it; sibling model gemini-3.5-flash was 503-overloaded.** Stopped hammering the API.
**Next / handoff:** M3 is functionally complete and verified EXCEPT the last 2 abstention confirmations, blocked purely by today's free-tier quota (not a code/quality issue). To finish: tomorrow (quota resets) or with headroom, run `python -m app.ingest`… no — `python -m app.eval.run_eval --llm` (now throttled + retrying) and confirm `appstore-dau` + `msft-cfo-salary` abstain. Then M3 is done. Live UI click-through of a cited answer also still wants an eyeball once quota allows. `main` green. Did NOT commit (per protocol). Suggested commit: `fix: m3 retrieval recall→1.0 (OR keyword + company-name strip), grouped-citation parsing, working Gemini model`.
**Roadmap:** M3 — ticked hybrid retrieval (recall 1.00), grounded answer endpoint, AI panel UI. Faithfulness box left at "strong, 2 abstentions pending quota."

---

### 2026-06-18 — Sally (Opus)
**Prompted to:** Double-check Alexander's M3 work and leave a clean resume point (James low on usage; deferring the two fixes).
**Did:** Verified the M3 build — all files present (chunks/embeddings/retrieve/answer/ask/reader/eval + golden_qa.json), migration `0004` sequential (down_revision 0003), `.env.example` has the 4 new RAG vars. Confirmed Alexander's gate behavior was correct (diagnosed weak recall, probe-validated fix, stopped — did not tune blindly).
**Verified:** Files read directly (sandbox git view was glitching — trust file reads, not bash git here). M3 is NOT committed — flagged to James to commit the green WIP from his own terminal.
**Next / handoff:** Two items remain to close M3, both documented in Alexander's entry below: (1) apply the OR-based keyword fix in `app/rag/retrieve.py` (probe says recall@8 → ~1.0), then RE-RUN `python -m app.eval.run_eval` to confirm actual recall ≥0.9; (2) add `GEMINI_API_KEY` to `.env` and run `python -m app.eval.run_eval --llm` for faithfulness (must be ~100% supported + correct abstention on the 3 unanswerable Qs). Then commit M3 as done. Resume from these two; everything else is built and green.
**Roadmap:** No change — M3 partial (A–E built; recall fix + faithfulness pending), as Alexander left it.

---

### 2026-06-18 — Alexander (Claude Code)
**Prompted to:** Build Milestone 3 (the wedge) slices A→E continuously, keep main green/committable, STOP at F (evals) and report recall + faithfulness before declaring done. Locked seams: Gemini 2.0 Flash, bge-small-en-v1.5 (384d local), section-aware sub-chunks, RRF. Refinements: cache key includes provider+model; bge query-prefix asymmetry; strict grounding + ≥2–3 unanswerable Qs.
**Did:**
- **A (chunking):** `app/ingest/chunks.py` (section-aware sub-chunks, ~3k chars/400 overlap, absolute offsets, content-hash) + `app/ingest/chunk.py` CLI (idempotent, embedding-preserving upsert). Migration `0004`: `filing_chunks` (vector(384) + GENERATED tsvector/GIN + HNSW cosine), `ai_interactions`, `answer_cache` (unique key incl. provider+model). Golden test `test_chunking.py`. → 4,770 chunks / 19 filings.
- **B (embeddings):** `app/embeddings.py` seam — bge passages plain, QUERY gets "Represent this sentence for searching relevant passages:" prefix; lazy/cached model. `app/ingest/embed.py` CLI (embeds NULL-embedding chunks only). All 4,770 embedded. Added `pgvector`, CPU-`torch`+`sentence-transformers` to requirements (CPU-torch note).
- **C (retrieval):** `app/rag/retrieve.py` — pgvector cosine + Postgres FTS, RRF (k=60), pre-filtered by filing.
- **D (grounded answer):** `app/llm/` provider seam (gemini + deterministic `mock`); `app/rag/answer.py` (answer-only-from-chunks, [n] citations → chunk char ranges, abstains "Not stated in the filings.", no-retrieval short-circuit); `POST /filing/{accession}/ask` with answer_cache + ai_interactions logging. `test_grounding.py` (offline, injected fake LLM).
- **E (UI):** `apps/web/.../reader.tsx` client component — "Ask this filing" panel; footnote [n] deep-links + highlights the exact source char range in the reader. `next build` clean.
- **F (evals):** Self-validating golden set `tests/golden_qa.json` (13 Qs: 10 answerable w/ verbatim source spans + 3 unanswerable) + `app/eval/run_eval.py` (recall@k always, faithfulness when key present) + structural pytest.
**Verified:** `pytest` 25/25 green; `next build` clean; mock end-to-end ask → fresh→cached→404 + logging confirmed; live hybrid retrieval returns on-target Item 1A chunks. Stored content_text is clean UTF-8 (U+2019, zero U+FFFD — the console `�` is cp1252 display only). **recall@8 = 0.60 (6/10) — WEAK.** Faithfulness NOT run (no GEMINI_API_KEY).
**Next / handoff:** STOPPED at F gate per instruction (report before tuning). **Diagnosed the weak recall:** the keyword half is effectively dead — `websearch_to_tsquery` ANDs all query terms, so natural-language questions almost never match (kw_rank=None on all 4 misses); system was running semantic-only, leaving 2 owners at rank 36–40 and missing 2. **Read-only probe confirms the fix:** OR-based keyword (`to_tsquery` with `|`-joined content terms) ranks all 4 missed owner-chunks at 1–2 → projected recall@8 ≈ 1.0 via RRF. Awaiting James's go to apply (RAG path — go slow). Faithfulness needs his free AI Studio key, then `python -m app.eval.run_eval --llm`. Did NOT commit. Suggested commits per slice in session report. `.env.example` still needs the new LLM/embedding vars (pending).
**Roadmap:** Milestone 3 — ticked chunking, embeddings, golden Q&A set, ai_interactions+answer_cache. Hybrid retrieval / grounded endpoint / AI panel / faithfulness boxes left open pending the keyword fix + a live faithfulness run.

---

### 2026-06-18 — Alexander (Claude Code)
**Prompted to:** Write the lead-engineer succession manual before Milestone 3, then a handoff showing where the next Alexander should look.
**Did:** Added `docs/ALEXANDER.md` — role/responsibilities, architecture-as-it-is (monorepo, FastAPI/Next/Postgres+pgvector, 3 processes/ports, migrations 0001–0003), engineering conventions, hard-won gotchas, the correctness-over-speed standard, and the team/WORKLOG protocol. Added `docs/M3_BOOTSTRAP.md` — GPS coordinates: read these 6 docs/code files in order to understand the data you're chunking (filing_sections + immutable content_text), the decision seams (LLM provider, embeddings, chunking, retrieval fusion), and the 8 M3 checkboxes you must deliver.
**Verified:** Docs only; no code touched. main still green.
**Next / handoff:** Milestone 3 not started — awaiting James's go. Next Alexander: start with M3_BOOTSTRAP.md.
**Roadmap:** No checkboxes changed.

---

### 2026-06-19 — Bobby (Sonnet 4.6)
**Prompted to:** Add a free Gemini API key to the project so AI features can run.
**Did:**
- Confirmed `.env` is gitignored (line 2 of `.gitignore`) — key is safe.
- Added `GEMINI_API_KEY=` line to `.env` under a new `# LLM API keys` section.
- James restarted uvicorn to pick up the new env var — confirmed working.
**Verified:** James confirmed services back up after uvicorn restart.
**Next / handoff:** Gemini key is in place. Project is ready for Sally to prompt Alexander on Milestone 3 (RAG pipeline — chunking, embeddings, hybrid retrieval, cited answer endpoint + UI). Key format starts with `AQ.` — if Alexander hits an auth error, double-check the key value in `.env`.
**Roadmap:** No milestone changes — M3 not yet started.

---

### 2026-06-18 — Alexander (Claude Code)
**Prompted to:** Milestone 2 — store filing document text, segment 10-K sections, filing list + reader on the company page.
**Did:**
- Schema + migration `0003`: `filing_documents` (1:1 cleaned text) + `filing_sections` (code/title/order + char offsets). Hand-written; existing tables untouched.
- `app/ingest/sections.py` (HTML→text via bs4 + 10-K Item segmentation), `storage.py` (`DocumentStore` seam — Postgres impl now, R2 later), `documents.py` CLI (`python -m app.ingest.documents`). Caches raw HTML to `data/edgar/filings/`.
- Segmentation skips the TOC by requiring a non-empty same-line title (verified against real AAPL 10-K); `content_text` immutable except on `--refresh`, which re-segments in the same pass (stable offsets for M3 citations).
- API: `/company/{ticker}` now returns a `filings` list; new `/filing/{accession_no}` returns text + sections. Frontend: Filings card + `/filing/[accession]` reader with section nav.
- Golden test (`tests/test_filing_sections.py`) on a real AAPL FY2023 10-K text fixture: Item 1A Risk Factors present (~67.9k chars), Item 7 MD&A present, ordered/non-overlapping, TOC not mistaken for body; + html→text unit test.
**Verified:** Ingested docs for all 10 (latest 2×10-K + 2×10-Q each); 10-Ks → 22–23 sections, 10-Qs stored unsegmented. Idempotent re-run skips. `pytest` 9/9 green. `next build` clean. End-to-end: `/company/aapl` filings list → 10-K reader shows Risk Factors/MD&A via anchor nav.
**Next / handoff:** Milestone 3 (the wedge) — section-aware chunking + embeddings (pgvector) + hybrid retrieval + grounded cited answers, built on `filing_sections` char offsets. GOTCHAs: (1) XOM/JPM incorporate MD&A by reference → stub Item 7 in the primary doc (faithful, content lives in an exhibit we don't fetch). (2) 10-Q is unsegmented (Part-aware codes deferred). (3) Only latest 2 10-Ks/company ingested — the AAPL FY2023 fixture filing itself isn't in the DB. Did NOT commit — James to commit (messages in summary).
**Roadmap:** Milestone 2 — all 4 checkboxes ticked.

---

### 2026-06-18 — Alexander (Claude Code)
**Prompted to:** Milestone 1 — SEC ingestion + company page for 10 tickers (AAPL MSFT NVDA GOOGL AMZN META JPM KO XOM UNH). No AI, no auth.
**Did:**
- Schema + migration `0002`: `companies`, `filings`, `financials` (tall facts; `filed_date` added for audit). Hand-fixed autogenerate that wanted to drop `health_check`.
- Ingestion CLI in `services/api/app/ingest/` (`edgar.py` cache+throttle+UA-from-env, `concepts.py` map, `parse.py`, `run.py`). Caches raw EDGAR JSON to `data/edgar/` (gitignored); idempotent upserts on natural keys.
- XBRL parse rule: `fiscal_year` from period **end date** (not `fy`/`fp`); dedupe per (line_item, year) keeping latest-`filed`. Annual (10-K) only, USD only, full-year duration filter.
- API `GET /company/{ticker}` pivots tall → year-columns; Next.js `/company/[ticker]` server component renders 3 statement tables (5 yrs).
- Golden test (`tests/test_golden_financials.py`) on a real AAPL fixture: FY2023 Revenue 383,285M & NetIncome 96,995M, FY2021 365,817M (comparatives guard), no dupes.
**Verified:** Ingested all 10 (e.g. AAPL 264 financials). `pytest` 4/4 green. `next build` clean. End-to-end: `/company/aapl` HTML shows Apple Inc. + 383,285 / 96,995; unknown ticker → 404. JPM correctly lacks Current Assets/Liabilities (bank, unclassified) — expected.
**Next / handoff:** Milestone 2 — store raw 10-K/10-Q text → R2, `filing_sections` table + section segmentation, filing list + reader on the company page. Note: company page reads live API (`NEXT_PUBLIC_API_URL`); API must be running. `data/` is cached so re-ingest is offline unless `--refresh`. Did NOT commit — James to commit (suggested messages in session summary).
**Roadmap:** Milestone 1 — all 6 checkboxes ticked.

---

### 2026-06-18 — Bobby (Sonnet 4.6) [session 3]
**Prompted to:** Write the Bobby succession manual (`docs/BOBBY.md`).
**Did:** Created `docs/BOBBY.md` covering role/boundaries, full runtime (3 processes + ports), env files, npm workspaces, GitHub remote, common issues + fixes, how to guide James, and session protocol.
**Verified:** File written and readable at `docs/BOBBY.md`.
**Next / handoff:** No code changes. Manual is ready for the next Bobby instance.
**Roadmap:** No changes.

---

### 2026-06-18 — Bobby (Sonnet 4.6) [session 2]
**Prompted to:** Fix frontend not loading — `localhost:3000` showing `ERR_CONNECTION_REFUSED`.
**Did:**
- Diagnosed the issue: `npm run dev:web` had been Ctrl+C'd, so nothing was listening on port 3000. Docker and uvicorn were both fine.
- Walked James through rerunning `npm run dev:web` from the repo root and leaving the terminal running.
**Verified:** James confirmed with screenshot — Mosaic health page showing **API: ok / Database: ok** at 7:35 PM.
**Next / handoff:** Nothing broken. All three services running (Docker/Postgres, uvicorn/API, Next.js/frontend). Ready for Sally to hand Alexander the Milestone 1 prompt whenever James gives the go.
**Roadmap:** No changes — still at Milestone 0 complete, Milestone 1 not started.

---

### 2026-06-18 — Bobby (Sonnet 4.6)
**Prompted to:** Install Docker Desktop, run the Milestone 0 verify block, and push the repo to GitHub.
**Did:**
- Copied `.env.example` → `.env` and `apps/web/.env.local.example` → `apps/web/.env.local`.
- Guided James through Docker Desktop installation (AMD64), `docker compose up -d`, Python venv setup, `pip install`, `alembic upgrade head`, and `uvicorn` startup.
- Confirmed health check green: **API: ok / Database: ok** at localhost:3000.
- Committed (`feat: milestone 0 — skeleton health check (green)`, root commit `113a038`, 43 files).
- Created GitHub repo `jagalv/mosaic` and pushed — repo is now live.
**Verified:** James shared a screenshot of localhost:3000 showing both statuses green.
**Next / handoff:** Milestone 0 fully complete including GitHub push. ROADMAP "Push repo to GitHub" checkbox should be ticked. Ready for Milestone 1 — Sally to write the Alexander prompt when James gives the go.
**Roadmap:** Milestone 0 — GitHub push done (was the last open item).

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
