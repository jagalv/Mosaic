"""Offline tests for the public /ask rate limit + demo-mode gate (M5 deploy).

No DB, embeddings, or real LLM. The rate-limit helper is tested against a tiny
fake session; the /ask gate is tested through the router with the LLM call and
the counters monkeypatched, pinning the three behaviors that protect a public,
shared-quota endpoint:
  - over the cap  -> demo-mode (no LLM call, no count)
  - a cache hit   -> served free, never counted
  - an LLM error  -> demo-mode, NEVER a 500, never counted
A real Gemini call (non-empty retrieval) IS counted exactly once.
"""

import types

from fastapi.testclient import TestClient

import app.routers.ask as ask_mod
from app.db import get_session
from app.main import app
from app.rag.answer import Citation
from app.rate_limit import GLOBAL_CAP, IP_CAP, over_cap, record_call


# --- rate-limit helper: pure cap logic + the upsert shape ---

class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value


class _CountDB:
    """Returns canned counts from .execute(...).scalar(), in order."""

    def __init__(self, counts):
        self._counts = list(counts)
        self.executed = []
        self.commits = 0

    def execute(self, stmt, params=None):
        self.executed.append((str(stmt), params))
        return _ScalarResult(self._counts.pop(0) if self._counts else 0)

    def commit(self):
        self.commits += 1


def test_over_cap_true_when_global_cap_reached():
    db = _CountDB([GLOBAL_CAP])  # global check alone trips it
    assert over_cap(db, "1.2.3.4") is True
    assert len(db.executed) == 1  # short-circuits before the per-IP query


def test_over_cap_true_when_ip_cap_reached():
    db = _CountDB([0, IP_CAP])  # global under, this IP at its cap
    assert over_cap(db, "1.2.3.4") is True


def test_over_cap_false_under_both_caps():
    db = _CountDB([0, IP_CAP - 1])
    assert over_cap(db, "1.2.3.4") is False


def test_record_call_upserts_ip_and_global_then_commits():
    db = _CountDB([])
    record_call(db, "1.2.3.4")
    assert len(db.executed) == 2  # per-IP row + GLOBAL row
    assert all("ON CONFLICT" in sql for sql, _ in db.executed)
    assert db.commits == 1


# --- /ask gate: routed behavior with the LLM + counters stubbed ---

class _FakeCache:
    abstained = False
    answer = "Cached answer. [1]"
    retrieved_chunk_ids = []
    unsupported_numbers = []


class _GateDB:
    """Minimal session: hands back queued .scalar() values (filing, doc, cache),
    no-op .execute()/.add()/.commit(). Suggestions query returns nothing."""

    def __init__(self, *, cache_hit):
        filing = types.SimpleNamespace(id=1, accession_no="x")
        self._scalars = [filing, 1, _FakeCache() if cache_hit else None]
        self.added = []

    def scalar(self, stmt):
        return self._scalars.pop(0)

    def execute(self, stmt, params=None):
        return _AllResult([])

    def add(self, obj):
        self.added.append(obj)

    def commit(self):
        pass

    def close(self):
        pass


class _AllResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


def _client(db, monkeypatch, *, record_spy):
    def _get_session_override():
        yield db
    app.dependency_overrides[get_session] = _get_session_override
    monkeypatch.setattr(
        ask_mod, "get_llm_client",
        lambda: types.SimpleNamespace(provider="gemini", model="gemini-2.5-flash-lite"),
    )
    monkeypatch.setattr(ask_mod, "client_ip", lambda request: "1.2.3.4")
    monkeypatch.setattr(ask_mod, "record_call", record_spy)
    return TestClient(app)


def _post(client):
    return client.post("/filing/x/ask", json={"question": "What were net sales?"})


def _live_result():
    return types.SimpleNamespace(
        answer="Net sales were $X. [1]",
        abstained=False,
        citations=[Citation(marker=1, chunk_id=7, section_code="item7",
                            char_start=0, char_end=5)],
        unsupported_numbers=[],
        retrieved=[types.SimpleNamespace(id=7)],
        model="gemini-2.5-flash-lite",
        prompt_tokens=1,
        completion_tokens=1,
        latency_ms=5,
    )


def test_over_cap_returns_demo_mode_without_calling_llm(monkeypatch):
    calls = {"record": 0}
    monkeypatch.setattr(ask_mod, "over_cap", lambda db, ip: True)

    def _boom(*a, **k):  # must not run when over the cap
        raise AssertionError("answer_question must not be called over the cap")
    monkeypatch.setattr(ask_mod, "answer_question", _boom)

    client = _client(_GateDB(cache_hit=False), monkeypatch,
                     record_spy=lambda db, ip: calls.__setitem__("record", calls["record"] + 1))
    resp = _post(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["demo_mode"] is True and "suggestions" in body
    assert calls["record"] == 0  # nothing counted
    app.dependency_overrides.clear()


def test_cache_hit_served_free_and_not_counted(monkeypatch):
    calls = {"record": 0}
    monkeypatch.setattr(ask_mod, "over_cap",
                        lambda db, ip: (_ for _ in ()).throw(
                            AssertionError("cap must not be checked on a cache hit")))
    client = _client(_GateDB(cache_hit=True), monkeypatch,
                     record_spy=lambda db, ip: calls.__setitem__("record", calls["record"] + 1))
    resp = _post(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body["cached"] is True and body.get("demo_mode") is None
    assert calls["record"] == 0
    app.dependency_overrides.clear()


def test_llm_error_degrades_to_demo_mode_not_500(monkeypatch):
    calls = {"record": 0}
    monkeypatch.setattr(ask_mod, "over_cap", lambda db, ip: False)

    def _raise(*a, **k):
        raise RuntimeError("429 RESOURCE_EXHAUSTED PerDay")
    monkeypatch.setattr(ask_mod, "answer_question", _raise)

    client = _client(_GateDB(cache_hit=False), monkeypatch,
                     record_spy=lambda db, ip: calls.__setitem__("record", calls["record"] + 1))
    resp = _post(client)
    assert resp.status_code == 200  # NOT a 500
    assert resp.json()["demo_mode"] is True
    assert calls["record"] == 0  # a failed call is not counted
    app.dependency_overrides.clear()


def test_real_gemini_call_is_counted_once(monkeypatch):
    calls = {"record": 0}
    monkeypatch.setattr(ask_mod, "over_cap", lambda db, ip: False)
    monkeypatch.setattr(ask_mod, "answer_question", lambda *a, **k: _live_result())

    client = _client(_GateDB(cache_hit=False), monkeypatch,
                     record_spy=lambda db, ip: calls.__setitem__("record", calls["record"] + 1))
    resp = _post(client)
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("demo_mode") is None and body["cached"] is False
    assert calls["record"] == 1  # exactly one real call counted
    app.dependency_overrides.clear()
