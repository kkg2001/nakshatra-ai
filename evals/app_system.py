"""The real app pipeline as a system under test (compare against evals.baseline)."""
from __future__ import annotations

from backend.app.llm.base import LLMClient
from backend.app.pipeline import answer_question
from evals.schema import Case


def app_answer(client: LLMClient, case: Case) -> str:
    return answer_question(client, case.profile, case.question, case.persona)["answer"]
