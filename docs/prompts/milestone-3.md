# Milestone 3 Build Prompt — for Alexander (Claude Code)

> Lead-AI note (Sally): this is a strong DRAFT from the previous Sally. Before sending it,
> re-read the current ROADMAP/WORKLOG/DECISIONS in case anything changed, refine if needed,
> and after Alexander posts his plan, REVIEW it with James before approving — especially the
> chunking strategy, the grounding/citation prompt, and the eval thresholds. This is the
> wedge: a weak design here quietly produces convincing-but-wrong answers. Trust is the spine.
>
> Two things James must provide before Alexander runs: a free LLM API key (default Gemini
> Flash) set in `.env`, and acceptance of heavier Python deps (local embeddings pull in
> sentence-transformers/torch). Both are flagged as decisions in the prompt below.

---

```
Milestone 3 — "Ask this filing" (THE WEDGE). Full repo access; you auto-load CLAUDE.md,
README, ROADMAP, DECISIONS, WORKLOG. Don't restate the project. This is the feature the
whole product exists for and the README calls the thesis — correctness and trust beat speed.

== OPERATING METHOD ==
1. ORIENT. Read the docs + the code you'll build on: models, migrations 0001-0003,
   filing_documents/filing_sections (esp. the immutable content_text + char offsets),
   the /filing reader. Establish built vs missing for retrieval/AI.
2. CONFIRM SCOPE vs ROADMAP Milestone 3: section-aware chunking + metadata → embeddings in
   pgvector → hybrid retrieval (vector + full-text, RRF) → grounded answer endpoint that
   CITES sources and abstains when unsupported → AI panel that deep-links each citation to
   the source paragraph in the reader → an eval gate (golden Q&A: retrieval recall + answer
   faithfulness). Roadmap wins on any conflict.
3. PLAN ONLY — then STOP. Post: chunking strategy + chunk schema, embedding choice, the
   retrieval/fusion design, the grounding+citation prompt, the eval set + thresholds, schema
   delta/migration, API + UI changes. >>> NO code until I reply "approved". <<<

== DECISIONS TO SURFACE (don't silently pick; recommend + await my call) ==
A. EMBEDDINGS: local sentence-transformers (e.g. bge-small-en-v1.5, 384-dim) = $0, offline,
   no rate limits, but adds heavy deps (torch). vs a free embedding API = lighter deps but
   network/rate limits. Recommend + note the dependency weight. Pin whatever you choose.
B. LLM PROVIDER for generation: cheap-first, behind a provider-agnostic interface so it's
   swappable. Default Gemini Flash (free tier); key read from a new env var (e.g.
   GEMINI_API_KEY) — add to .env.example, James sets the real key locally. Never hardcode.

== THE HARD PART — grounding & citations (own it; the eval gate pins it) ==
- Chunk WITHIN sections (don't cross section boundaries); carry metadata
  {cik, ticker, accession_no, form_type, section_code, char_start, char_end} where the
  offsets index into the immutable content_text — so each citation deep-links to the exact
  paragraph in the existing reader. Reasonable size + overlap; hash content (no re-embed).
- Hybrid retrieval: pgvector semantic + Postgres full-text (tsvector), fused via RRF,
  PRE-FILTERED by company/filing/section before ranking. Small top-k.
- Generation prompt: answer ONLY from retrieved context; every claim cites a chunk id;
  if the context doesn't support an answer, say "not stated in the filings" — do NOT use
  outside/memorized knowledge, and NEVER emit a number that isn't in the retrieved text.
- Stream the answer; render footnotes that link into the reader at the cited char range.

== SCHEMA (new migration, sequential, hand-written; don't disturb existing tables) ==
- chunks (id, filing_id, cik, form_type, section_code, content, tsv generated, embedding
  vector, char_start, char_end, content_hash) + appropriate indexes (HNSW/ivfflat + GIN tsv).
  Corpus is tiny — exact search is acceptable; add an index only if needed, note the choice.
- ai_interactions (question, answer, retrieved_chunk_ids, model, tokens, latency, feedback).
- answer_cache (key = hash(question+filing+model) → answer + citations, ttl).

== EVAL GATE (non-negotiable for the wedge) ==
Build a golden Q&A set (~10-20 Qs with known answers + the source span) over a couple of
companies (use AAPL/MSFT 10-Ks that ARE ingested — note: the FY2023 fixture filing is NOT
in the DB). Measure retrieval (recall@k: did we fetch the right chunk?) SEPARATELY from
generation (faithfulness: is every claim supported? abstains correctly on unanswerable Qs).
Report the numbers. If faithfulness is weak, STOP and tell me — do not ship a confident-but-
wrong wedge.

== DONE WHEN ==
Filings chunked + embedded; hybrid retrieval works; grounded endpoint answers with citations
that deep-link to the reader and abstains when unsupported; AI panel on the company/filing
page; eval set passes your stated thresholds; pytest green; next build clean; end-to-end
verified on a real question (e.g. AAPL risk factors). Protocol: WORKLOG + ROADMAP M3 boxes +
DECISIONS (embedding, LLM provider, index choice). Suggest commits; do not commit.

End with: what runs, the eval numbers, how to verify, what's deferred, recommended next.
```
