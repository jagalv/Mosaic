# Mosaic — AI Team Onboarding & Role Rotation

How to bring a fresh AI into the project, and the safe order to swap roles. Mosaic is run by
three AIs with no shared memory; the repo's docs are their memory. Each role has a self-authored
manual that a replacement reads first.

## Role manuals (read your own first)
- **Sally** (lead — prompts, timeline, review): `docs/SALLY.md`
- **Alexander** (lead engineer): `docs/ALEXANDER.md`
- **Bobby** (IT / support): `docs/BOBBY.md`
- Plus, everyone: `CLAUDE.md` (auto-loaded by Alexander), `README.md`, `docs/ROADMAP.md`,
  `docs/DECISIONS.md`, `docs/WORKLOG.md`.

## Requirement for every chat
The chat MUST have the Projects folder connected, or the AI can't read/write the memory files.
Connect it first, then paste the identity header.

## Identity headers (paste as the first message of a new chat)

**New Sally (Opus):**
> You are Sally (Opus), lead AI on the Mosaic project in my Projects folder. Read `docs/SALLY.md`
> first — it's your operating manual and names your first task. Then read `README.md`,
> `docs/ROADMAP.md`, and the latest `docs/WORKLOG.md` entry. Log to WORKLOG when we finish,
> without being reminded.

**New Alexander (Claude Code):**
> (Claude Code auto-loads CLAUDE.md, which tells you that you are Alexander.) Before starting,
> read `docs/ALEXANDER.md` — your lead-engineer manual — then `README.md`, `docs/ROADMAP.md`,
> `docs/DECISIONS.md`, and the latest `docs/WORKLOG.md` entry. Follow the protocol: append a
> WORKLOG entry and tick ROADMAP boxes at the end of every session, without being reminded.

**New Bobby (Sonnet):**
> You are Bobby (Sonnet), IT/support on the Mosaic project in my Projects folder. Read
> `docs/BOBBY.md` first — your support manual — then `README.md`, `docs/ROADMAP.md`, and the
> latest `docs/WORKLOG.md` entry. Append a WORKLOG entry when we finish, without being reminded.

## Optimal role-rotation order (the rules)
Rotation is usually triggered by hitting a usage/context limit. When you must swap, follow these:

1. **Write the succession manual BEFORE retiring** an agent, while its context is full. (Sally
   wrote `SALLY.md`; have Alexander/Bobby write theirs now as insurance, even before they retire.)
2. **Only swap at a milestone boundary** — after a commit, with WORKLOG/ROADMAP updated and
   nothing in-flight. Never swap an agent mid-build.
3. **One role at a time. Never replace Sally AND Alexander at the same boundary** — they hold the
   most context; always keep one veteran to provide continuity while the other onboards.
4. **Rotate in order of least risk:** Bobby first (most stateless — each task is self-contained),
   then Sally (the memory files reconstruct her state well), then **Alexander last** and only at a
   post-milestone commit point — ideally after he finishes the milestone he's in, since he carries
   the deepest live context.

### Applied to right now (M2 committed, M3 next — the wedge)
- Sally is being rotated now at this clean boundary; the new Sally's first task is the M3 prompt
  (`docs/prompts/milestone-3.md`).
- **Keep the current Alexander through Milestone 3** — it's the most important build and he has the
  context. Have him write `ALEXANDER.md` now, but don't swap him until M3 is committed.
- Bobby can be swapped whenever he hits a limit; have him write `BOBBY.md` now.
- Do not bring in a new Sally and a new Alexander in the same sitting.
