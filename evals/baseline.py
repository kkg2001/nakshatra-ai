"""The deliberately naive baseline: one generic prompt, no tools, no RAG, no guardrails.
Every later improvement is measured against this."""
from __future__ import annotations

from backend.app.llm.base import LLMClient
from evals.schema import Case

BASELINE_SYSTEM = "You are an astrologer. Answer the user's question."


def build_user_message(case: Case) -> str:
    p = case.profile
    return (
        f"My name is {p.name}. Born on {p.dob}"
        f"{', at ' + p.tob if p.tob else ''}{', in ' + p.pob if p.pob else ''}.\n\n"
        f"{case.question}"
    )


def baseline_answer(client: LLMClient, case: Case) -> str:
    return client.generate(BASELINE_SYSTEM, build_user_message(case))
