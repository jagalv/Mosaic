"""Grounded answer generation — the trust spine of Milestone 3.

Pipeline: retrieve chunks for the question within ONE filing -> build a strictly
grounded prompt with numbered excerpts -> ask the LLM -> map the [n] citations
back to chunk ids + char ranges so the UI can deep-link into the reader.

Grounding contract (James's refinement #3), enforced by prompt + parsing:
  - Answer ONLY from the provided excerpts; no outside knowledge.
  - Cite every claim with [n] referencing the excerpt number(s).
  - If the excerpts don't support an answer, reply EXACTLY
    "Not stated in the filings." and nothing else.
  - Never assert a number/date/fact not present verbatim in the excerpts.

If retrieval returns nothing, we abstain WITHOUT calling the LLM — there is
literally no ground to stand on. Faithfulness of the model itself is measured in
the golden eval; this module guarantees the scaffolding around it.
"""

import re
import time
from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.llm import LLMClient, get_llm_client
from app.rag.guard import unsupported_numbers
from app.rag.retrieve import DEFAULT_TOP_K, RetrievedChunk, retrieve

ABSTAIN_TEXT = "Not stated in the filings."

SYSTEM_PROMPT = (
    "You are a careful financial-research assistant. You answer questions about "
    "a SINGLE SEC filing using ONLY the numbered excerpts provided.\n\n"
    "Rules — follow them exactly:\n"
    "1. Use ONLY information stated in the excerpts. Never use outside knowledge.\n"
    "2. Cite every claim with [n] markers referencing the excerpt number(s) that "
    "support it. Put the citation right after the claim.\n"
    "3. Never state a number, date, name, or fact that does not appear verbatim "
    "in the excerpts.\n"
    f"4. If the excerpts do not contain enough information to answer, reply with "
    f"EXACTLY this and nothing else: {ABSTAIN_TEXT}\n"
    "5. Be concise. Do not speculate, hedge, or add caveats beyond the excerpts."
)

# Match a citation bracket that may group several numbers, e.g. [1], [1, 2],
# [1,2,3]. Models routinely group citations; matching only [\d] silently drops
# them (answer looks uncited, and the UI gets no deep-link).
_CITATION_RE = re.compile(r"\[([\d,\s]+)\]")


@dataclass(frozen=True)
class Citation:
    marker: int  # the [n] used in the answer
    chunk_id: int
    section_code: str
    char_start: int
    char_end: int


@dataclass(frozen=True)
class AnswerResult:
    answer: str
    abstained: bool
    citations: list[Citation]
    # Significant figures in `answer` not found in the retrieved text. Non-empty
    # => the caller flags-and-warns (the answer is still shown — see guard.py).
    unsupported_numbers: list[str]
    retrieved: list[RetrievedChunk]  # everything retrieved (for logging/debug)
    provider: str
    model: str
    prompt_tokens: int | None
    completion_tokens: int | None
    latency_ms: int


def _build_user_prompt(question: str, chunks: list[RetrievedChunk]) -> str:
    blocks = []
    for i, c in enumerate(chunks, start=1):
        blocks.append(f"[{i}] (Section {c.section_code}):\n{c.content_text.strip()}")
    excerpts = "\n\n".join(blocks)
    return (
        f"Question: {question}\n\n"
        f"Excerpts from the filing:\n\n{excerpts}\n\n"
        f"Answer the question using only these excerpts, with [n] citations."
    )


def _is_abstention(text: str) -> bool:
    norm = re.sub(r"[\s.]+", " ", text).strip().lower()
    return norm == re.sub(r"[\s.]+", " ", ABSTAIN_TEXT).strip().lower()


def _extract_citations(
    answer: str, chunks: list[RetrievedChunk]
) -> list[Citation]:
    seen: set[int] = set()
    cites: list[Citation] = []
    for m in _CITATION_RE.finditer(answer):
        for part in m.group(1).split(","):
            part = part.strip()
            if not part.isdigit():
                continue
            n = int(part)
            if 1 <= n <= len(chunks) and n not in seen:
                seen.add(n)
                c = chunks[n - 1]
                cites.append(
                    Citation(
                        marker=n,
                        chunk_id=c.id,
                        section_code=c.section_code,
                        char_start=c.char_start,
                        char_end=c.char_end,
                    )
                )
    return cites


def answer_question(
    session: Session,
    filing_id: int,
    question: str,
    top_k: int = DEFAULT_TOP_K,
    llm_client: LLMClient | None = None,
) -> AnswerResult:
    """Retrieve, ground, and answer a question about one filing."""
    client = llm_client or get_llm_client()
    started = time.perf_counter()

    chunks = retrieve(session, filing_id, question, top_k=top_k)
    if not chunks:
        # Nothing retrieved -> abstain without spending an LLM call.
        return AnswerResult(
            answer=ABSTAIN_TEXT,
            abstained=True,
            citations=[],
            unsupported_numbers=[],
            retrieved=[],
            provider=getattr(client, "provider", "unknown"),
            model=getattr(client, "model", "unknown"),
            prompt_tokens=0,
            completion_tokens=0,
            latency_ms=int((time.perf_counter() - started) * 1000),
        )

    result = client.generate(SYSTEM_PROMPT, _build_user_prompt(question, chunks))
    abstained = _is_abstention(result.text)
    citations = [] if abstained else _extract_citations(result.text, chunks)
    # Numbers guard: verify every significant figure traces to the retrieved
    # text. An abstention has no figures to check.
    unsupported = (
        []
        if abstained
        else unsupported_numbers(
            result.text, "\n".join(c.content_text for c in chunks)
        )
    )

    return AnswerResult(
        answer=result.text,
        abstained=abstained,
        citations=citations,
        unsupported_numbers=unsupported,
        retrieved=chunks,
        provider=getattr(client, "provider", "unknown"),
        model=result.model,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens,
        latency_ms=int((time.perf_counter() - started) * 1000),
    )
