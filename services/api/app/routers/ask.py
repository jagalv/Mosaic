"""Ask-this-filing endpoint: POST /filing/{accession_no}/ask.

Grounded Q&A over a single filing. Wraps app.rag.answer with the two
persistence concerns the roadmap calls for:

  answer_cache       — repeated question on a filing returns instantly. The key
                       includes provider + model (James's refinement): swapping
                       LLM_MODEL never serves an answer from a different model.
  ai_interactions    — every call is logged (cache hits flagged) with retrieved
                       chunk ids, latency, and tokens for observability.

Citations carry char ranges so the frontend can deep-link straight into the
reader's source text.
"""

import hashlib

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.db import get_session
from app.llm import get_llm_client
from app.models import AiInteraction, AnswerCache, Filing, FilingDocument
from app.rag.answer import answer_question
from app.rate_limit import client_ip, over_cap, record_call

router = APIRouter()

# Shown when the shared daily Gemini budget is spent (rate cap or provider 429).
_DEMO_MODE_MESSAGE = (
    "This live demo runs on a shared free-tier model with a small daily "
    "question budget, which is currently used up — so this question wasn't sent "
    "to the model. Try one of the pre-answered showcase questions below; they "
    "always work."
)


def _demo_mode_response(db: Session, provider: str, model: str) -> dict:
    """A friendly, additive demo-mode payload (never a 500). `suggestions` are
    drawn from REAL cached, non-abstained answers, so every one is guaranteed to
    resolve instantly as a cache hit (the pre-seeded showcase Q&As)."""
    rows = db.execute(
        text(
            "SELECT c.ticker, f.accession_no, ac.question "
            "FROM answer_cache ac "
            "JOIN filings f ON f.id = ac.filing_id "
            "JOIN companies c ON c.cik = f.cik "
            "WHERE ac.abstained = false "
            "ORDER BY ac.created_at DESC "
            "LIMIT 3"
        )
    ).all()
    suggestions = [
        {"ticker": r.ticker, "accession_no": r.accession_no, "question": r.question}
        for r in rows
    ]
    return {
        "answer": _DEMO_MODE_MESSAGE,
        "abstained": False,
        "citations": [],
        "unsupported_numbers": [],
        "cached": False,
        "provider": provider,
        "model": model,
        "latency_ms": 0,
        "demo_mode": True,
        "suggestions": suggestions,
    }


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


def _question_hash(question: str) -> str:
    norm = " ".join(question.strip().lower().split())
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()


def _log_interaction(
    db: Session,
    *,
    filing_id: int,
    question: str,
    answer: str,
    chunk_ids: list[int],
    provider: str,
    model: str,
    latency_ms: int,
    prompt_tokens: int | None,
    completion_tokens: int | None,
    abstained: bool,
    unsupported_numbers: list[str],
    cached: bool,
) -> None:
    db.add(
        AiInteraction(
            filing_id=filing_id,
            question=question,
            answer=answer,
            retrieved_chunk_ids=chunk_ids,
            provider=provider,
            model=model,
            latency_ms=latency_ms,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            abstained=abstained,
            unsupported_numbers=unsupported_numbers,
            cached=cached,
        )
    )
    db.commit()


@router.post("/filing/{accession_no}/ask")
def ask_filing(
    accession_no: str,
    body: AskRequest,
    request: Request,
    db: Session = Depends(get_session),
) -> dict:
    filing = db.scalar(select(Filing).where(Filing.accession_no == accession_no))
    if filing is None:
        raise HTTPException(status_code=404, detail=f"Filing {accession_no} not found")
    if db.scalar(
        select(FilingDocument.id).where(FilingDocument.filing_id == filing.id)
    ) is None:
        raise HTTPException(
            status_code=404, detail=f"Filing {accession_no} has no ingested document"
        )

    client = get_llm_client()
    provider, model = client.provider, client.model
    qhash = _question_hash(body.question)

    cached = db.scalar(
        select(AnswerCache).where(
            AnswerCache.filing_id == filing.id,
            AnswerCache.question_hash == qhash,
            AnswerCache.provider == provider,
            AnswerCache.model == model,
        )
    )
    if cached is not None:
        # `retrieved_chunk_ids` holds the citation objects (JSON) for this cache.
        citations = cached.retrieved_chunk_ids or []
        unsupported = cached.unsupported_numbers or []
        _log_interaction(
            db,
            filing_id=filing.id,
            question=body.question,
            answer=cached.answer,
            chunk_ids=[c["chunk_id"] for c in citations],
            provider=provider,
            model=model,
            latency_ms=0,
            prompt_tokens=0,
            completion_tokens=0,
            abstained=bool(cached.abstained),
            unsupported_numbers=unsupported,
            cached=True,
        )
        return {
            "answer": cached.answer,
            "abstained": bool(cached.abstained),
            "citations": citations,
            "unsupported_numbers": unsupported,
            "cached": True,
            "provider": provider,
            "model": model,
            "latency_ms": 0,
        }

    # Cache MISS -> the live path. It's anonymous and burns the shared Gemini
    # budget, so guard it: over the per-IP OR global cap -> demo-mode (no LLM
    # call); any LLM failure (e.g. a per-day 429) -> demo-mode, NEVER a 500.
    ip = client_ip(request)
    if over_cap(db, ip):
        return _demo_mode_response(db, provider, model)

    try:
        result = answer_question(db, filing.id, body.question, llm_client=client)
    except Exception:
        # The 404s above are raised before this block, so we don't mask them.
        return _demo_mode_response(db, provider, model)

    # Count only a REAL Gemini call: a non-empty retrieval means generate() ran.
    # An empty retrieval abstains without spending the budget (answer.py), so it
    # stays free and uncounted.
    if result.retrieved:
        record_call(db, ip)

    citations = [
        {
            "marker": c.marker,
            "chunk_id": c.chunk_id,
            "section_code": c.section_code,
            "char_start": c.char_start,
            "char_end": c.char_end,
        }
        for c in result.citations
    ]

    db.add(
        AnswerCache(
            filing_id=filing.id,
            question_hash=qhash,
            provider=provider,
            model=result.model,
            question=body.question,
            answer=result.answer,
            retrieved_chunk_ids=citations,
            abstained=result.abstained,
            unsupported_numbers=result.unsupported_numbers,
        )
    )
    _log_interaction(
        db,
        filing_id=filing.id,
        question=body.question,
        answer=result.answer,
        chunk_ids=[c.id for c in result.retrieved],
        provider=provider,
        model=result.model,
        latency_ms=result.latency_ms,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        abstained=result.abstained,
        unsupported_numbers=result.unsupported_numbers,
        cached=False,
    )

    return {
        "answer": result.answer,
        "abstained": result.abstained,
        "citations": citations,
        "unsupported_numbers": result.unsupported_numbers,
        "cached": False,
        "provider": provider,
        "model": result.model,
        "latency_ms": result.latency_ms,
    }
