# M3 Bootstrap — Where to Start

You are about to build Milestone 3: the wedge. "Ask this filing" — section-aware chunking,
embeddings, hybrid retrieval, grounded answers with citations. Before you plan, read these
files **in this order**. This is your GPS.

## 1. The request & acceptance criteria

**Read:** `docs/ROADMAP.md` — Milestone 3 section (the 8 checkboxes are the contract).

**Tl;dr:** You're building a Q&A system over filing sections. Answer only from retrieved
context; cite chunk IDs; return "not stated in the filings" when unsupported. The demo is
asking a real question about a real filing and getting a cited answer that deep-links to
the source paragraph.

## 2. The data you're building on

**Read:** `docs/WORKLOG.md` — the Milestone 2 entry (2026-06-18, Alexander), section
"**Verified**" and "**Next / handoff**".

**What you have:**
- `filing_documents` table: one row per filing, `content_text` (immutable cleaned text),
  `fetched_at`.
- `filing_sections` table: one row per section, holds `section_code`, `title`, `char_start`,
  `char_end` (offsets into that `content_text`).
- 10-K fully segmented (22–23 sections per company); 10-Q unsegmented (text only, no sections).
- Golden test: `tests/test_filing_sections.py` on a real AAPL FY2023 10-K fixture.

**Gotchas:** XOM/JPM have stub Item 7 (MD&A by reference, faithful but not in primary doc).
Only latest 2 10-Ks per company are ingested. The fixture filing itself may not be in the DB.

## 3. The code you must understand

All in `services/api/`:

| Path | What | Why you need it |
|---|---|---|
| `app/models.py` | `FilingDocument`, `FilingSection` ORM models | The tables you're querying |
| `alembic/versions/0003_*.py` | Schema for `filing_documents` + `filing_sections` | How char offsets work |
| `app/ingest/storage.py` | `DocumentStore` protocol + `PostgresDocumentStore` | The seam; understand the interface |
| `app/routers/filing.py` | `GET /filing/{accession_no}` endpoint | How the API serves text + sections |
| `app/ingest/sections.py` | Segmentation logic, especially `segment_10k()` | How sections are carved from text |
| `services/api/tests/test_filing_sections.py` | Golden test on real fixture | Understand the contract: offsets are stable |

**In `apps/web/`:**

| Path | What |
|---|---|
| `app/filing/[accession]/page.tsx` | Reader UX; shows sections with nav |
| `lib/api.ts` | `fetchFiling()` and types | The client-side contract |

## 4. The immutable contract

**This is load-bearing. Do not skip.** Read `docs/DECISIONS.md`, entry "Section segmentation:
TOC-skip by same-line title; content_text immutable". Then read the GOTCHAS section of
`docs/ALEXANDER.md`.

**In short:** `content_text` never changes once stored (except `--refresh`). When you chunk
for embeddings, you must preserve char offsets so **M3 citations can deep-link into the
original text by character range** (line `char_start`–`char_end` in `filing_sections`).

If you ever re-derive or mutate stored text without re-segmenting, you silently corrupt every
citation. This is not a guideline; it's a fatal flaw if broken.

## 5. The decision-making seams

Before you plan, understand where James will ask you to choose:

1. **LLM provider** (Gemini Flash / Groq / Claude). Given $0 goal; pick the cheapest that
   works. Document in env as `LLM_PROVIDER`, code behind a seam.
2. **Embeddings** (local `bge-small` / `e5-small` / `BAAI/bge-large-en-v1.5`). Local = $0,
   no rate limits, clean bulk ingestion. But: dimension choice (384 vs 768) affects pgvector
   index size. Decide upfront; document in `EMBEDDING_MODEL` env.
3. **Chunking strategy.** Section-aware (one chunk per section? sub-section chunks?) vs.
   fixed-size with overlap. Sections have natural boundaries; exploit them.
4. **Retrieval fusion.** pgvector (semantic) + Postgres full-text (keyword); RRF (reciprocal
   rank fusion) or a simple score blend? Both work; decide on complexity tradeoff.

Raise these in your plan; James will guide.

## 6. You're ready

Now read the M3 section of `ROADMAP.md` one more time. Notice the "done when" boxes:

- ✓ Section-aware chunking with metadata
- ✓ Embed chunks → pgvector; content-hash dedupe
- ✓ Hybrid retrieval (pgvector + full-text RRF, pre-filtered)
- ✓ Grounded answer endpoint (cite or "not stated")
- ✓ AI panel UI with footnotes + deep-links to source
- ✓ Golden Q&A set (10–20 real questions + source spans)
- ✓ Faithfulness + retrieval recall@k checks
- ✓ `ai_interactions` log + `answer_cache`

Your job: plan a vertical slice that lands all 8 of these. The "wedge" is the entire demo,
not a MVP. Ship the full thing, or don't ship.

**Post the plan. Wait for approval. Then build.**

---

*Breadcrumbs laid by Alexander on 2026-06-18.*
