from __future__ import annotations

from backend.app.llm.base import LLMClient, LLMError


class FallbackClient:
    """Try providers in order; move on when one fails (e.g. free-tier quota exhausted)."""

    def __init__(self, clients: list[LLMClient]):
        self.clients = clients
        self.name = "fallback(" + "|".join(c.name for c in clients) + ")"

    def generate(self, system: str, user: str, temperature: float | None = None) -> str:
        errors = []
        for c in self.clients:
            try:
                return c.generate(system, user, temperature)
            except LLMError as exc:
                errors.append(f"{c.name}: {exc}")
        raise LLMError("; ".join(errors))
