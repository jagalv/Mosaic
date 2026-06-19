"""Structural guard for the golden Q&A set (offline; no DB/LLM).

Keeps the eval set from rotting: well-formed JSON, unique ids, enough coverage,
and the answerable/unanswerable invariants. Span-existence + recall +
faithfulness are measured by `python -m app.eval.run_eval` against the live DB.
"""

import json
from pathlib import Path

GOLDEN = Path(__file__).parent / "golden_qa.json"


def _questions():
    return json.loads(GOLDEN.read_text(encoding="utf-8"))["questions"]


def test_set_is_well_formed_and_has_coverage():
    qs = _questions()
    answerable = [q for q in qs if not q["unanswerable"]]
    unanswerable = [q for q in qs if q["unanswerable"]]
    assert 10 <= len(qs) <= 20
    assert len(answerable) >= 7
    assert len(unanswerable) >= 2  # James's refinement #3: confirm it abstains


def test_ids_unique_and_fields_present():
    qs = _questions()
    assert len({q["id"] for q in qs}) == len(qs)
    for q in qs:
        assert q["question"].strip()
        assert q["accession"].strip()
        assert isinstance(q["answer_spans"], list)


def test_answerable_have_spans_unanswerable_do_not():
    for q in _questions():
        if q["unanswerable"]:
            assert q["answer_spans"] == []
        else:
            assert q["answer_spans"], f"{q['id']} needs at least one answer_span"
