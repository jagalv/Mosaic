"""LLM provider seam.

Everything the RAG layer needs from an LLM is one call: given a system
instruction and a user message, return text + token counts. Providers
(Gemini today; Groq/Claude/Ollama are drop-in) implement `LLMClient`; the rest
of the app depends only on this interface, so swapping LLM_PROVIDER never
touches the grounding code.
"""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class LLMResult:
    text: str
    model: str
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMClient(Protocol):
    provider: str
    model: str

    def generate(self, system: str, user: str) -> LLMResult: ...
