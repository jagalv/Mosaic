"""Numbers-guard tests — the trust spine's last line of defense.

Pure + offline. Covers the supported case, the fabricated case (the one that
matters), formatting robustness, the >=4-digit threshold, and that the guard
trips inside answer_question while flag-and-warn leaves the answer intact.
"""

import app.rag.answer as answer_mod
from app.rag.answer import answer_question
from app.rag.guard import unsupported_numbers
from app.rag.retrieve import RetrievedChunk


def _chunk(text: str, cid: int = 1) -> RetrievedChunk:
    return RetrievedChunk(
        id=cid,
        section_code="item7",
        char_start=0,
        char_end=len(text),
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


# ---- pure guard ----

def test_supported_number_passes():
    excerpt = "Total net sales were $383,285 in 2025."
    assert unsupported_numbers("Revenue was $383,285 million [1].", excerpt) == []


def test_fabricated_number_is_flagged():
    excerpt = "Total net sales were $383,285; net income was $96,995."
    assert unsupported_numbers("Net income was $999,999 million [1].", excerpt) == [
        "999999"
    ]


def test_formatting_differences_do_not_false_positive():
    # commas, $, and a 'million' suffix all reduce to the same digit core.
    excerpt = "net sales of 383,285"
    assert unsupported_numbers("$383,285 million", excerpt) == []
    assert unsupported_numbers("383285", excerpt) == []


def test_small_numbers_and_percentages_ignored():
    # below the >=4-digit threshold — these collide spuriously, so we don't guard them.
    assert unsupported_numbers("Margin was 16% and up 5 points [1].", "Margin moved.") == []


def test_year_is_guarded_both_ways():
    excerpt = "Fiscal 2025 results."
    assert unsupported_numbers("In 2025 revenue rose [1].", excerpt) == []
    assert unsupported_numbers("In 2099 revenue rose [1].", excerpt) == ["2099"]


def test_citation_markers_are_not_treated_as_numbers():
    # [1234] would be a 4-digit core if not stripped as a citation first.
    assert unsupported_numbers("See [1234].", "no figures here") == []


# ---- integration: guard inside answer_question (flag-and-warn keeps the answer) ----

def test_answer_question_flags_fabricated_number(monkeypatch):
    chunks = [_chunk("Net sales were 383,285 and net income 96,995 in 2025.")]
    monkeypatch.setattr(answer_mod, "retrieve", lambda *a, **k: chunks)
    res = answer_question(
        None,
        filing_id=1,
        question="What was net income?",
        llm_client=_FakeClient("Net income was 96,995, and cash was 555,444. [1]"),
    )
    assert not res.abstained
    # flag-and-warn: the answer text is unchanged, the figure is reported.
    assert res.answer == "Net income was 96,995, and cash was 555,444. [1]"
    assert res.unsupported_numbers == ["555444"]


def test_answer_question_clean_when_all_supported(monkeypatch):
    chunks = [_chunk("Net sales were 383,285 and net income 96,995 in 2025.")]
    monkeypatch.setattr(answer_mod, "retrieve", lambda *a, **k: chunks)
    res = answer_question(
        None,
        filing_id=1,
        question="What was net income?",
        llm_client=_FakeClient("Net income was 96,995. [1]"),
    )
    assert res.unsupported_numbers == []
