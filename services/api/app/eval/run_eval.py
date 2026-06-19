"""Milestone 3 RAG eval: retrieval recall@k and (optionally) faithfulness.

Two questions, reported separately so we know WHICH half to fix:

  recall@k     — does retrieval surface the passage that contains the answer?
                 Pure retrieval; needs no LLM. Scored by checking whether any
                 retrieved chunk contains a verbatim `answer_span`.

  faithfulness — does the grounded answer behave? Needs the LLM (GEMINI_API_KEY).
                 * answerable Q: answers (doesn't abstain) AND cites a chunk that
                   actually contains an answer_span (the citation supports it).
                 * unanswerable Q: abstains ("not stated in the filings").
                 An answerable Q whose supporting chunk wasn't retrieved is a
                 retrieval miss, not an unfaithful answer — there the faithful
                 behavior is to abstain, and we credit that.

Every answer_span is checked to exist in the real filing text first; a stale
span (e.g. after re-ingest) is reported, not silently scored against.

Usage (from services/api, venv active):
    python -m app.eval.run_eval            # recall@k only
    python -m app.eval.run_eval --llm      # recall@k + faithfulness (needs key)
    python -m app.eval.run_eval --k 5
"""

import json
import sys
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import Filing, FilingDocument
from app.rag.answer import answer_question
from app.rag.retrieve import retrieve

# app/eval/run_eval.py -> app/eval -> app -> services/api (where tests/ lives)
GOLDEN = Path(__file__).resolve().parents[2] / "tests" / "golden_qa.json"

# Seconds between LLM calls. The Gemini free tier is ~10 requests/minute, so we
# pace at <10/min to avoid 429s during the eval. Harmless when keys have headroom.
LLM_THROTTLE_SECONDS = 7.0


def _load():
    data = json.loads(GOLDEN.read_text(encoding="utf-8"))
    return data["questions"]


def _filing_id(session: Session, accession: str) -> int | None:
    return session.scalar(
        select(Filing.id).where(Filing.accession_no == accession)
    )


def _doc_text(session: Session, filing_id: int) -> str:
    return session.scalar(
        select(FilingDocument.content_text).where(
            FilingDocument.filing_id == filing_id
        )
    )


def _validate_spans(session: Session, questions: list[dict]) -> list[str]:
    """Confirm every answer_span exists in its filing. Returns problem strings."""
    problems: list[str] = []
    for q in questions:
        if q["unanswerable"]:
            continue
        fid = _filing_id(session, q["accession"])
        if fid is None:
            problems.append(f"{q['id']}: filing {q['accession']} not ingested")
            continue
        text = _doc_text(session, fid)
        for span in q["answer_spans"]:
            if span not in text:
                problems.append(f"{q['id']}: span not found -> {span!r}")
    return problems


def _chunk_has_span(text: str, spans: list[str]) -> bool:
    return any(span in text for span in spans)


def run(use_llm: bool, k: int) -> int:
    questions = _load()
    answerable = [q for q in questions if not q["unanswerable"]]
    unanswerable = [q for q in questions if q["unanswerable"]]
    print(
        f"Golden set: {len(questions)} questions "
        f"({len(answerable)} answerable, {len(unanswerable)} unanswerable), k={k}\n"
    )

    with SessionLocal() as session:
        problems = _validate_spans(session, questions)
        if problems:
            print("SPAN VALIDATION PROBLEMS (scored items skipped):")
            for p in problems:
                print(f"  ! {p}")
            print()

        # ---- Retrieval recall@k ----
        recall_hits = 0
        recall_scored = 0
        recall_detail: list[tuple[str, bool]] = []
        retrieved_cache: dict[str, list] = {}
        for q in answerable:
            fid = _filing_id(session, q["accession"])
            if fid is None:
                continue
            chunks = retrieve(session, fid, q["question"], top_k=k)
            retrieved_cache[q["id"]] = chunks
            hit = any(
                _chunk_has_span(c.content_text, q["answer_spans"]) for c in chunks
            )
            recall_scored += 1
            recall_hits += int(hit)
            recall_detail.append((q["id"], hit))

        print("RETRIEVAL recall@%d" % k)
        for qid, hit in recall_detail:
            print(f"  {'HIT ' if hit else 'MISS'}  {qid}")
        recall = recall_hits / recall_scored if recall_scored else 0.0
        print(f"  recall@{k} = {recall_hits}/{recall_scored} = {recall:.2f}\n")

        if not use_llm:
            print("Faithfulness: SKIPPED (pass --llm with GEMINI_API_KEY set).")
            return 0

        # ---- Faithfulness (needs the LLM) ----
        try:
            from app.llm import get_llm_client

            client = get_llm_client()
        except Exception as exc:  # no key / bad provider
            print(f"Faithfulness: SKIPPED — {exc}")
            return 0

        print(f"FAITHFULNESS (provider={client.provider}, model={client.model})")
        ans_correct = 0
        for i, q in enumerate(answerable):
            if i:
                time.sleep(LLM_THROTTLE_SECONDS)  # respect free-tier rate limit
            fid = _filing_id(session, q["accession"])
            res = answer_question(session, fid, q["question"], top_k=k, llm_client=client)
            recall_hit = any(
                _chunk_has_span(c.content_text, q["answer_spans"])
                for c in res.retrieved
            )
            cited_support = any(
                _chunk_has_span(
                    next(rc.content_text for rc in res.retrieved if rc.id == c.chunk_id),
                    q["answer_spans"],
                )
                for c in res.citations
            )
            if recall_hit:
                ok = (not res.abstained) and cited_support  # should answer + support
            else:
                ok = res.abstained  # supporting passage missing -> abstain is faithful
            ans_correct += int(ok)
            tag = "OK " if ok else "BAD"
            mode = "answered" if not res.abstained else "abstained"
            print(f"  {tag}  {q['id']}: {mode}, recall_hit={recall_hit}, cites={len(res.citations)}")
            if not ok:  # show what the model actually said, for diagnosis
                print(f"        raw: {res.answer[:160]!r}")

        abstain_correct = 0
        for q in unanswerable:
            time.sleep(LLM_THROTTLE_SECONDS)  # respect free-tier rate limit
            fid = _filing_id(session, q["accession"])
            res = answer_question(session, fid, q["question"], top_k=k, llm_client=client)
            ok = res.abstained
            abstain_correct += int(ok)
            print(f"  {'OK ' if ok else 'BAD'}  {q['id']}: {'abstained' if res.abstained else 'ANSWERED (should abstain!)'}")
            if not ok:
                print(f"        raw: {res.answer[:160]!r}")

        total = len(answerable) + len(unanswerable)
        faithful = ans_correct + abstain_correct
        print(
            f"\n  answerable behaved: {ans_correct}/{len(answerable)}"
            f"  ·  unanswerable abstained: {abstain_correct}/{len(unanswerable)}"
        )
        print(f"  faithfulness = {faithful}/{total} = {faithful / total:.2f}")
    return 0


def main(argv: list[str]) -> int:
    use_llm = "--llm" in argv
    k = 8
    if "--k" in argv:
        i = argv.index("--k")
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            k = int(argv[i + 1])
    return run(use_llm, k)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
