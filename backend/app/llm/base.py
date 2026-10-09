"""The one contract every LLM provider must satisfy. App and evals depend only on this."""
from __future__ import annotations

from typing import Protocol


class LLMError(Exception):
    """Raised when a provider call fails after retries."""


class LLMClient(Protocol):
    name: str

    def generate(self, system: str, user: str, temperature: float | None = None) -> str: ...
