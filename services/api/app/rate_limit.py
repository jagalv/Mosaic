"""Per-IP + global daily rate limiting for the public /ask endpoint (M5 deploy).

The "Ask this filing" endpoint is anonymous and runs on a SHARED Gemini free
tier (~20 requests/day on ONE key, across ALL visitors). So the GLOBAL daily
soft-cap is the real protection — set below Gemini's ceiling so the API flips to
demo-mode deterministically BEFORE the provider 429s. The per-IP cap is a
courtesy throttle that stops a single visitor monopolizing the shared budget.

Only REAL Gemini calls are counted: the caller invokes `record_call` after a
non-empty retrieval (a cache hit or a no-retrieval abstain spends nothing, so it
stays free and uncounted). Counts live in `ask_rate_limit` (migration 0010) so
they survive a Space restart/sleep, unlike an in-memory counter.

This runs on the mosaic_app session WITHOUT a user GUC (the endpoint is
anonymous); `ask_rate_limit` has no RLS, so that's fine.
"""

import hashlib
from datetime import datetime, timezone

from fastapi import Request
from sqlalchemy import text
from sqlalchemy.orm import Session

# Live Gemini questions allowed per client IP per UTC day (courtesy throttle).
IP_CAP = 3
# Live Gemini questions across ALL visitors per UTC day. Kept below Gemini's
# ~20/day free ceiling so demo-mode kicks in before the provider errors.
GLOBAL_CAP = 18
# Sentinel ip_hash for the single global counter row.
GLOBAL_KEY = "GLOBAL"


def client_ip(request: Request) -> str:
    """Best-effort client IP. Behind the HF Spaces proxy the real client is the
    FIRST entry of X-Forwarded-For; fall back to the socket peer. XFF is
    client-spoofable, so the per-IP cap is a courtesy throttle — the global cap
    and the pre-cached showcase are the real guarantees."""
    xff = request.headers.get("x-forwarded-for")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    return request.client.host if request.client else "unknown"


def _hash_ip(ip: str) -> str:
    # Store a hash, not the raw IP (mild-PII hygiene for a public endpoint).
    return hashlib.sha256(ip.encode("utf-8")).hexdigest()


def _today_utc():
    return datetime.now(timezone.utc).date()


def _count(db: Session, key: str, day) -> int:
    row = db.execute(
        text("SELECT count FROM ask_rate_limit WHERE ip_hash = :k AND day = :d"),
        {"k": key, "d": day},
    ).scalar()
    return int(row or 0)


def over_cap(db: Session, ip: str) -> bool:
    """True if EITHER the global soft-cap or this IP's daily cap is already
    reached. Checked BEFORE any live Gemini call; True => serve demo-mode."""
    day = _today_utc()
    if _count(db, GLOBAL_KEY, day) >= GLOBAL_CAP:
        return True
    return _count(db, _hash_ip(ip), day) >= IP_CAP


def record_call(db: Session, ip: str) -> None:
    """Increment the per-IP and global counters for ONE real Gemini call. Upsert
    so the first call of the day inserts and the rest add one."""
    day = _today_utc()
    for key in (_hash_ip(ip), GLOBAL_KEY):
        db.execute(
            text(
                "INSERT INTO ask_rate_limit (ip_hash, day, count) "
                "VALUES (:k, :d, 1) "
                "ON CONFLICT (ip_hash, day) "
                "DO UPDATE SET count = ask_rate_limit.count + 1"
            ),
            {"k": key, "d": day},
        )
    db.commit()
