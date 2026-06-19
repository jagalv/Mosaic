"""Gemini provider (google-genai SDK).

Chosen for Milestone 3: free tier, good instruction-following for grounded,
cited answers. Temperature 0 — for grounded extraction we want the most
faithful, least creative continuation. The client is imported lazily by the
factory so the SDK + key are only required when the provider is actually used.

Free-tier resilience: the Gemini free tier caps requests per minute, so a burst
returns 429 RESOURCE_EXHAUSTED. We retry a bounded number of times, honoring the
server's suggested retry delay, so a transient rate limit doesn't surface as a
500 to the user (or abort a batch eval).
"""

import re
import time

from app.config import get_settings
from app.llm.base import LLMResult

_MAX_RETRIES = 3
_DEFAULT_RETRY_SECONDS = 20.0
_MAX_RETRY_SECONDS = 60.0


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
                # A per-DAY cap won't clear on a short retry — fail fast instead
                # of sleeping. Only retry per-minute / transient rate limits.
                per_day = "PerDay" in msg or "per day" in msg
                if not is_429 or per_day or attempt == _MAX_RETRIES:
                    raise
                time.sleep(_retry_after_seconds(err))

        usage = getattr(resp, "usage_metadata", None)
        return LLMResult(
            text=(resp.text or "").strip(),
            model=self.model,
            prompt_tokens=getattr(usage, "prompt_token_count", None),
            completion_tokens=getattr(usage, "candidates_token_count", None),
        )
