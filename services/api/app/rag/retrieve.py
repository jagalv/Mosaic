"""Hybrid retrieval for Milestone 3: pgvector semantic + Postgres full-text, RRF.

Two retrievers, fused by Reciprocal Rank Fusion (James's call): each returns a
ranked candidate list for the same query, scoped to ONE filing, and we combine
them by rank position rather than by raw score. RRF needs no score
normalization across the (incomparable) cosine-distance and ts_rank scales,
which is exactly why it's robust here.

  semantic: embed the query with bge's instruction prefix, order chunks by
            cosine distance (HNSW, vector_cosine_ops).
  keyword:  OR-tsquery of the question's content terms over the DB-maintained
            `tsv` column, ranked by ts_rank.
  fuse:     score(c) = sum over retrievers of 1 / (RRF_K + rank_in_that_list).

Keyword design note (recall fix, 2026-06-19): the keyword half used to AND every
query term (`websearch_to_tsquery`), so a natural-language question almost never
matched any chunk and the system ran effectively semantic-only (recall@8=0.60).
We now lowercase the question, drop stopwords, and OR-join the remaining content
terms into a `to_tsquery`. ts_rank still orders by relevance, so an exact phrase
("effective tax rate") surfaces its chunk at the top. The semantic retriever is
untouched and remains the fallback when a query has no usable keyword terms.

Pre-filtering by filing_id is mandatory — "Ask this filing" answers from one
document, never bleeds across companies. (Section pre-filtering is supported via
`section_codes` but unused by the default endpoint.)
"""

import re
from collections import defaultdict
from dataclasses import dataclass

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.embeddings import embed_query
from app.models import Company, Filing, FilingChunk

# Generic English stopwords dropped before building the keyword OR-query. These
# are function/question words that carry no retrieval signal; ts_rank handles
# the rest. (We deliberately keep domain nouns like "company"/"apple" — ts_rank
# down-weights ubiquitous terms on its own.)
_STOPWORDS = frozenset(
    """
    a an the of to in on for and or but if then else when where why how which who
    whom whose what that this these those is are was were be been being am do does
    did doing have has had having will would shall should can could may might must
    as at by from into onto with within without about above below over under again
    further once here there all any both each few more most other some such no nor
    not only own same so than too very s t can it its it's their them they we you
    your our us my me he she his her about over per via
    """.split()
)

_WORD_RE = re.compile(r"[a-z0-9]+")


def _keyword_terms(query: str, extra_stop: frozenset[str] = frozenset()) -> list[str]:
    """Lowercase, tokenize, drop stopwords/short tokens -> content terms.

    `extra_stop` carries the filing's own company-name tokens: in single-filing
    retrieval the company name appears in nearly every chunk, so as a keyword it
    is pure noise that (with ts_rank's lack of IDF) drowns the chunk holding the
    actual answer. Dropping it is what moves recall, not cosmetics.
    """
    seen: set[str] = set()
    terms: list[str] = []
    for tok in _WORD_RE.findall(query.lower()):
        if (
            len(tok) > 2
            and tok not in _STOPWORDS
            and tok not in extra_stop
            and tok not in seen
        ):
            seen.add(tok)
            terms.append(tok)
    return terms


def _company_stop_tokens(session: Session, filing_id: int) -> frozenset[str]:
    """The filing's company name/ticker tokens — noise words for keyword search."""
    row = session.execute(
        select(Company.name, Company.ticker)
        .join(Filing, Filing.cik == Company.cik)
        .where(Filing.id == filing_id)
    ).first()
    if row is None:
        return frozenset()
    name, ticker = row
    toks = set(_WORD_RE.findall((name or "").lower()))
    if ticker:
        toks.add(ticker.lower())
    return frozenset(toks)

# RRF constant. 60 is the canonical default (Cormack et al.); it damps the
# influence of any single retriever's top ranks so the two lists blend smoothly.
RRF_K = 60
# Candidate pool size per retriever before fusion.
DEFAULT_POOL = 40
# Final chunks handed to the LLM.
DEFAULT_TOP_K = 8


@dataclass(frozen=True)
class RetrievedChunk:
    id: int
    section_code: str
    char_start: int
    char_end: int
    content_text: str
    rrf_score: float
    semantic_rank: int | None  # 1-based; None if not in the semantic list
    keyword_rank: int | None


def _semantic_ids(
    session: Session,
    filing_id: int,
    qvec: list[float],
    pool: int,
    section_codes: list[str] | None,
) -> list[int]:
    q = select(FilingChunk.id).where(
        FilingChunk.filing_id == filing_id,
        FilingChunk.embedding.isnot(None),
    )
    if section_codes:
        q = q.where(FilingChunk.section_code.in_(section_codes))
    q = q.order_by(FilingChunk.embedding.cosine_distance(qvec)).limit(pool)
    return list(session.scalars(q).all())


def _keyword_ids(
    session: Session,
    filing_id: int,
    query: str,
    pool: int,
    section_codes: list[str] | None,
    extra_stop: frozenset[str] = frozenset(),
) -> list[int]:
    # `tsv` is a DB-generated column not mapped on the ORM model, so this is raw
    # SQL. We build an OR query from sanitized content terms; tokens are
    # [a-z0-9]+ only (no tsquery operators), so `to_tsquery` can't be injected.
    terms = _keyword_terms(query, extra_stop)
    if not terms:
        return []  # no usable keyword signal -> semantic retriever carries it
    orq = " | ".join(terms)

    section_clause = ""
    params = {"fid": filing_id, "q": orq, "pool": pool}
    if section_codes:
        section_clause = "AND section_code = ANY(:codes)"
        params["codes"] = section_codes
    sql = text(
        f"""
        SELECT id
        FROM filing_chunks
        WHERE filing_id = :fid
          {section_clause}
          AND tsv @@ to_tsquery('english', :q)
        ORDER BY ts_rank(tsv, to_tsquery('english', :q)) DESC
        LIMIT :pool
        """
    )
    return [row[0] for row in session.execute(sql, params).all()]


def retrieve(
    session: Session,
    filing_id: int,
    query: str,
    top_k: int = DEFAULT_TOP_K,
    pool: int = DEFAULT_POOL,
    section_codes: list[str] | None = None,
) -> list[RetrievedChunk]:
    """Return the top_k chunks for `query` within `filing_id`, RRF-fused."""
    qvec = embed_query(query)
    company_stop = _company_stop_tokens(session, filing_id)
    sem = _semantic_ids(session, filing_id, qvec, pool, section_codes)
    kw = _keyword_ids(session, filing_id, query, pool, section_codes, company_stop)

    sem_rank = {cid: i for i, cid in enumerate(sem, start=1)}
    kw_rank = {cid: i for i, cid in enumerate(kw, start=1)}

    scores: dict[int, float] = defaultdict(float)
    for cid, r in sem_rank.items():
        scores[cid] += 1.0 / (RRF_K + r)
    for cid, r in kw_rank.items():
        scores[cid] += 1.0 / (RRF_K + r)

    top_ids = sorted(scores, key=lambda c: scores[c], reverse=True)[:top_k]
    if not top_ids:
        return []

    rows = {
        c.id: c
        for c in session.scalars(
            select(FilingChunk).where(FilingChunk.id.in_(top_ids))
        ).all()
    }
    return [
        RetrievedChunk(
            id=cid,
            section_code=rows[cid].section_code,
            char_start=rows[cid].char_start,
            char_end=rows[cid].char_end,
            content_text=rows[cid].content_text,
            rrf_score=scores[cid],
            semantic_rank=sem_rank.get(cid),
            keyword_rank=kw_rank.get(cid),
        )
        for cid in top_ids
    ]
