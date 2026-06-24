"""Batch corpus ingestion orchestrator (M6a).

Runs the four idempotent ingestion stages IN ORDER for a set of tickers, reusing
the existing per-ticker functions (it does NOT reimplement ingestion):

    run.ingest_ticker -> documents.ingest_documents -> chunk.chunk_ticker
                      -> embed.embed_pending

One bad company never kills the run: each ticker is wrapped in try/except +
rollback and the batch continues. The whole run emits ONE consolidated report —
per stage: attempted / ok / failed-with-reason — plus the resulting DB state,
printed at the end and written to data/ingest_reports/<timestamp>.txt.

Idempotent + re-runnable: a partial/interrupted batch just converges on re-run
(natural-key upserts; warm SEC cache => no refetch).

Usage (from services/api, venv active; DATABASE_URL points at the TARGET DB):
    python -m app.ingest.batch                  # BATCH_20, latest 4 10-Ks each
    python -m app.ingest.batch AAPL MSFT        # an explicit subset
    python -m app.ingest.batch --limit-10k 2 --limit-10q 0
    python -m app.ingest.batch --refresh        # bypass the on-disk cache
"""

import sys
from datetime import datetime

from sqlalchemy import select

from app.config import REPO_ROOT
from app.db import SessionLocal
from app.ingest import edgar
from app.ingest.chunk import chunk_ticker
from app.ingest.documents import DEFAULT_LIMIT_10Q, ingest_documents
from app.ingest.embed import embed_pending
from app.ingest.qa import corpus_summary
from app.ingest.run import ingest_ticker
from app.ingest.sp100 import BATCH_20
from app.models import Company

REPORT_DIR = REPO_ROOT / "data" / "ingest_reports"
# This slice's depth: latest 4 10-Ks/company (~4 yrs) so M7 can show multi-year
# evolution, not a single diff.
BATCH_LIMIT_10K = 4


def _int_flag(argv: list[str], name: str, default: int) -> int:
    if name in argv:
        i = argv.index(name)
        if i + 1 < len(argv) and argv[i + 1].isdigit():
            return int(argv[i + 1])
    return default


def _run_per_ticker(session, label, tickers, call) -> dict:
    """Run `call(session, ticker)` for each ticker, isolating failures.

    Returns a stage record: {label, attempted, ok:[t], failed:[(t, reason)]}.
    """
    print(f"\n== {label}: {len(tickers)} ticker(s) ==")
    ok, failed = [], []
    for t in tickers:
        try:
            call(session, t)
            ok.append(t)
        except Exception as exc:  # one bad company must not kill the run
            session.rollback()
            reason = f"{type(exc).__name__}: {exc}"
            print(f"  {t:6s} FAILED: {reason}")
            failed.append((t, reason))
    return {"label": label, "attempted": len(tickers), "ok": ok,
            "failed": failed, "note": None}


def _format_report(meta: dict, stages: list[dict], summary: dict) -> str:
    lines = [
        "Mosaic corpus ingestion - batch report",
        f"when         : {meta['when']}",
        f"limits       : 10-K={meta['limit_10k']}  10-Q={meta['limit_10q']}  "
        f"refresh={meta['refresh']}",
        f"tickers ({len(meta['tickers']):2d}) : {' '.join(meta['tickers'])}",
        "",
        "Per-stage results:",
    ]
    for st in stages:
        lines.append(
            f"  [{st['label']:9s}] attempted={st['attempted']:>3}  "
            f"ok={len(st['ok']):>3}  failed={len(st['failed']):>3}"
            + (f"  ({st['note']})" if st.get("note") else "")
        )
        for t, reason in st["failed"]:
            lines.append(f"      FAIL {t}: {reason}")
    lines += ["", "Resulting corpus (DB state):"]
    for k, v in summary.items():
        lines.append(f"  {k:18s} {v}")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    refresh = "--refresh" in argv
    limit_10k = _int_flag(argv, "--limit-10k", BATCH_LIMIT_10K)
    limit_10q = _int_flag(argv, "--limit-10q", DEFAULT_LIMIT_10Q)
    tickers = [
        a.upper() for a in argv if not a.startswith("--") and not a.isdigit()
    ] or list(BATCH_20)

    started = datetime.now()
    print(f"Batch ingest: {len(tickers)} ticker(s) at {started:%Y-%m-%d %H:%M:%S} "
          f"(10-K={limit_10k}, 10-Q={limit_10q}, refresh={refresh})")

    tickers_data = edgar.fetch_company_tickers(refresh=refresh)
    stages: list[dict] = []

    with SessionLocal() as session:
        stages.append(_run_per_ticker(
            session, "run", tickers,
            lambda s, t: ingest_ticker(s, t, tickers_data, refresh),
        ))
        stages.append(_run_per_ticker(
            session, "documents", tickers,
            lambda s, t: ingest_documents(s, t, limit_10k, limit_10q, refresh),
        ))
        stages.append(_run_per_ticker(
            session, "chunk", tickers,
            lambda s, t: chunk_ticker(s, t),
        ))

        # Embed is a single batch pass (not per-ticker): fill every NULL vector
        # for the batch's companies with the local bge model.
        print("\n== embed: pending vectors for the batch ==")
        ciks = [
            cik for t in tickers
            if (cik := session.scalar(
                select(Company.cik).where(Company.ticker == t.upper())
            )) is not None
        ]
        embed_stage = {"label": "embed", "attempted": len(ciks), "ok": [],
                       "failed": [], "note": None}
        try:
            n = embed_pending(session, force=False, ciks=ciks or None)
            embed_stage["ok"] = ciks
            embed_stage["note"] = f"{n} chunk(s) embedded"
        except Exception as exc:
            session.rollback()
            reason = f"{type(exc).__name__}: {exc}"
            print(f"  embed FAILED: {reason}")
            embed_stage["failed"] = [("<embed>", reason)]
        stages.append(embed_stage)

        summary = corpus_summary(session)

    meta = {"when": f"{started:%Y-%m-%d %H:%M:%S}", "tickers": tickers,
            "limit_10k": limit_10k, "limit_10q": limit_10q, "refresh": refresh}
    report = _format_report(meta, stages, summary)

    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORT_DIR / f"batch_{started:%Y%m%d_%H%M%S}.txt"
    report_path.write_text(report + "\n", encoding="utf-8")

    print("\n" + report)
    print(f"\nReport written to {report_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
