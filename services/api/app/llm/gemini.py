"""Gemini provider (google-genai SDK).

Chosen for Milestone 3: free tier, good instruction-following for grounded,
cited answers. Temperature 0 — for grounded extraction we want the most
faithful, least creative continuation. The client is imported lazily by the
factory so the SDK + key are only required when the provider is actually used.

Free-tier resilience: the Gemini free tier caps requests per minute, so a burst
returns 429 RESOURCE_EXHAUSTED; the backend also returns transient 503
UNAVAILABLE ("model overloaded / high demand"). We retry both a bounded number of
times so a transient blip doesn't surface as a 500 to the user (or abort a batch
eval). The two get DIFFERENT budgets: a per-minute 429 honors the server's
suggested delay (which can be ~20s); a 503 gets a SHORT fixed backoff and a small
retry count so a user-facing request fails over to demo-mode in a few seconds
rather than hanging. A per-DAY 429 quota fails fast (a short retry won't clear it).
"""

import re
import time

from app.config import get_settings
from app.llm.base import LLMResult

_MAX_RETRIES = 3
_DEFAULT_RETRY_SECONDS = 20.0
_MAX_RETRY_SECONDS = 60.0
# 503 UNAVAILABLE is transient but user-facing: keep the total added wait to a
# few seconds (~2s x 2 retries) so we fail over to demo-mode fast.
_MAX_503_RETRIES = 2
_BACKOFF_503_SECONDS = 2.0


def _retry_after_seconds(err: Exception) -> float:
    """Pull the server's suggested retry delay out of a 429, else a default."""
    m = re.search(r"retry in (\d+(?:\.\d+)?)s", str(err)) or re.search(
        r"retryDelay['\":\s]+(\d+(?:\.\d+)?)s", str(err)
    )
    secs = float(m.group(1)) if m else _DEFAULT_RETRY_SECONDS
    return min(secs + 1.0, _MAX_RETRY_SECONDS)


class GeminiClient:
    provider = "gemini"

    def __init__(self) -> None:
        settings = get_settings()
        if not settings.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Add it to .env "
                "(free key: https://aistudio.google.com/apikey)."
            )
        from google import genai  # lazy: only when Gemini is actually used

        self.model = settings.llm_model
        self._client = genai.Client(api_key=settings.gemini_api_key)

    def generate(self, system: str, user: str) -> LLMResult:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system, temperature=0.0
        )
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=user, config=config
                )
                break
            except Exception as err:
                msg = str(err)
                is_429 = "429" in msg or "RESOURCE_EXHAUSTED" in msg
                is_503 = "503" in msg or "UNAVAILABLE" in msg
                # A per-DAY cap won't clear on a short retry — fail fast instead
                # of sleeping. Retry per-minute 429s and transient 503s only.
                per_day = "PerDay" in msg or "per day" in msg
                retryable = (is_429 and not per_day) or is_503
                # 503s get a SHORT fixed backoff + small budget so a degraded
                # backend fails over to demo-mode fast; 429s keep the larger
                # budget and the server-suggested delay. (A 503 that isn't also a
                # 429 takes the short path.)
                short = is_503 and not is_429
                max_retries = _MAX_503_RETRIES if short else _MAX_RETRIES
                if not retryable or attempt >= max_retries:
                    raise
                time.sleep(
                    _BACKOFF_503_SECONDS if short else _retry_after_seconds(err)
                )

        usage = getattr(resp, "usage_metadata", None)
        return LLMResult(
            text=(resp.text or "").strip(),
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_token_count", None),
            completion_tokens=getattr(usage, "candidates_token_count", None),
        )
