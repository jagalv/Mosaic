"""Deterministic offline LLM provider for tests and no-key local demos.

Returns a fixed, grounded-looking answer that cites [1] whenever excerpts are
present in the prompt. It does NOT reason — it exists so the request path
(prompt assembly, citation mapping, caching, logging) can be exercised without a
real key. True grounding/faithfulness is measured against the real model in the
golden eval (Slice F), never against this.
"""

from app.llm.base import LLMResult

MOCK_ANSWER = "This is a deterministic mock answer grounded in the filing. [1]"


class MockClient:
    provider = "mock"
    model = "mock-1"

    def generate(self, system: str, user: str) -> LLMResult:
        # If the prompt carried no excerpts, behave like an honest abstention.
        text = MOCK_ANSWER if "[1]" in user else "Not stated in the filings."
        return LLMResult(text=text, model=self.model, prompt_tokens=0, completion_tokens=0)
