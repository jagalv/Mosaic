"""Offline tests for GeminiClient.generate()'s retry policy (M5 503 fix).

No network, no API key, no real SDK calls: we build a GeminiClient WITHOUT going
through __init__ (which needs a key) and inject a fake `models` client that
raises canned errors. time.sleep is monkeypatched to record (not actually wait)
the backoffs. These pin the trust-spine-adjacent retry behavior:
  - a transient 503 is retried with a SHORT fixed backoff, then succeeds
  - a persistent 503 raises after a small, bounded number of short retries
  - a per-DAY 429 quota still fails fast (no retry) — unchanged
  - a non-retryable error (e.g. bad key) raises immediately — unchanged
On a raise, ask.py's except -> demo-mode (never a 500).
"""

import types

import pytest

import app.llm.gemini as gemini
from app.llm.gemini import (
    _BACKOFF_503_SECONDS,
    _MAX_503_RETRIES,
    GeminiClient,
)


class _FakeModels:
    """Raises queued errors on each call; returns `final` once they run out."""

    def __init__(self, errors, final=None):
        self._errors = list(errors)
        self._final = final
        self.calls = 0

    def generate_content(self, model, contents, config):
        self.calls += 1
        if self._errors:
            raise self._errors.pop(0)
        return self._final


def _client(errors, final=None):
    c = object.__new__(GeminiClient)  # skip __init__ (no key / no SDK client)
    c.model = "gemini-test"
    c._client = types.SimpleNamespace(models=_FakeModels(errors, final))
    return c


@pytest.fixture
def sleeps(monkeypatch):
    recorded: list[float] = []
    monkeypatch.setattr(gemini.time, "sleep", lambda s: recorded.append(s))
    return recorded


def _ok_response():
    return types.SimpleNamespace(text="Net sales were $X. [1]", usage_metadata=None)


def test_transient_503_is_retried_then_succeeds(sleeps):
    client = _client(
        [Exception("503 UNAVAILABLE: the model is overloaded, high demand")],
        final=_ok_response(),
    )
    result = client.generate("system", "user")
    assert result.text == "Net sales were $X. [1]"
    assert client._client.models.calls == 2  # one failure + one success
    assert sleeps == [_BACKOFF_503_SECONDS]  # SHORT fixed backoff, not the 429 delay


def test_persistent_503_raises_after_short_bounded_backoff(sleeps):
    client = _client([Exception("503 UNAVAILABLE") for _ in range(10)])
    with pytest.raises(Exception, match="503"):
        client.generate("system", "user")
    # Exactly the small 503 budget of retries, each a short fixed backoff.
    assert sleeps == [_BACKOFF_503_SECONDS] * _MAX_503_RETRIES
    assert client._client.models.calls == _MAX_503_RETRIES + 1
    assert sum(sleeps) <= 5.0  # total added latency stays a few seconds, not 20s+


def test_per_day_429_quota_still_fails_fast(sleeps):
    client = _client([Exception("429 RESOURCE_EXHAUSTED: quota exceeded PerDay")])
    with pytest.raises(Exception, match="429"):
        client.generate("system", "user")
    assert sleeps == []  # no retry, no sleep
    assert client._client.models.calls == 1


def test_non_retryable_error_raises_immediately(sleeps):
    client = _client([Exception("400 API key not valid")])
    with pytest.raises(Exception, match="API key not valid"):
        client.generate("system", "user")
    assert sleeps == []
    assert client._client.models.calls == 1
