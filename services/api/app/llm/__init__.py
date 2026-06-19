"""LLM provider factory: resolve LLM_PROVIDER -> a concrete LLMClient.

Cached so the SDK/client is constructed once per process. Add a provider by
implementing LLMClient and registering it here — nothing else changes.
"""

from functools import lru_cache

from app.config import get_settings
from app.llm.base import LLMClient, LLMResult

__all__ = ["LLMClient", "LLMResult", "get_llm_client"]


@lru_cache(maxsize=1)
def get_llm_client() -> LLMClient:
    provider = get_settings().llm_provider.lower()
    if provider == "gemini":
        from app.llm.gemini import GeminiClient

        return GeminiClient()
    if provider == "mock":
        from app.llm.mock import MockClient

        return MockClient()
    raise RuntimeError(f"Unknown LLM_PROVIDER: {provider!r} (expected gemini|mock)")
