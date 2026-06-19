"""Grounding-scaffold tests — the parts of the trust spine we CAN pin offline.

These don't touch the DB, embeddings, or a real LLM. They verify the
deterministic scaffolding around the model: citation [n] -> chunk mapping,
abstention detection, and the no-retrieval short-circuit. Model faithfulness
itself is measured against the real LLM in the golden eval (Slice F).
"""

import app.rag.answer as answer_mod
from app.rag.answer import (
    ABSTAIN_TEXT,
    _build_user_prompt,
    _extract_citations,
    _is_abstention,
    answer_question,
)
from app.rag.retrieve import RetrievedChunk


def _chunk(cid: int, code: str, start: int, end: int, text: str) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid,
        section_code=code,
        char_start=start,
        char_end=end,
        content_text=text,
        rrf_score=1.0,
        semantic_rank=1,
        keyword_rank=1,
    )


class _FakeClient:
    provider = "fake"
    model = "fake-1"

    def __init__(self, text: str) -> None:
        self._text = text

    def generate(self, system: str, user: str):
        from app.llm.base import LLMResult

        return LLMResult(text=self._text, model=self.model, prompt_tokens=1, completion_tokens=1)


def test_abstention_detection_tolerates_formatting():
    assert _is_abstention("Not stated in the filings.")
    assert _is_abstention("  not stated in the filings  ")
    assert not _is_abstention("The filing states revenue grew. [1]")


def test_citation_extraction_maps_markers_to_chunks():
    chunks = [
        _chunk(101, "item1a", 10, 20, "risk one"),
        _chunk(202, "item7", 30, 40, "mdna two"),
    ]
    cites = _extract_citations("Risk rose [1]. Margins fell [2]. Again [1].", chunks)
    assert [c.marker for c in cites] == [1, 2]  # deduped, order preserved
    assert cites[0].chunk_id == 101 and cites[0].char_start == 10
    assert cites[1].chunk_id == 202 and cites[1].section_code == "item7"


def test_citation_extraction_ignores_out_of_range_markers():
    chunks = [_chunk(101, "item1", 0, 5, "only one")]
    assert _extract_citations("Claim [3].", chunks) == []


def test_prompt_numbers_excerpts_from_one():
    chunks = [_chunk(1, "item1a", 0, 1, "alpha"), _chunk(2, "item7", 0, 1, "beta")]
    prompt = _build_user_prompt("What changed?", chunks)
    assert "[1] (Section item1a)" in prompt and "alpha" in prompt
    assert "[2] (Section item7)" in prompt and "beta" in prompt


def test_no_retrieval_abstains_without_calling_llm(monkeypatch):
    monkeypatch.setattr(answer_mod, "retrieve", lambda *a, **k: [])

    class _Boom:
        provider, model = "boom", "boom"

        def generate(self, system, user):  # pragma: no cover - must not run
            raise AssertionError("LLM must not be called when nothing is retrieved")

    res = answer_question(None, filing_id=1, question="anything", llm_client=_Boom())
    assert res.abstained and res.answer == ABSTAIN_TEXT and res.citations == []


def test_answer_maps_model_citations(monkeypatch):
    chunks = [_chunk(55, "item1a", 100, 200, "Supply chain is concentrated.")]
    monkeypatch.setattr(answer_mod, "retrieve", lambda *a, **k: chunks)
    res = answer_question(
        None,
        filing_id=1,
        question="What is a key risk?",
        llm_client=_FakeClient("Supply chain concentration is a risk. [1]"),
    )
    assert not res.abstained
    assert len(res.citations) == 1 and res.citations[0].chunk_id == 55
    assert res.citations[0].char_start == 100
