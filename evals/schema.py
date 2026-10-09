"""Typed schema for eval cases. One JSON object per line in datasets/*.jsonl."""
from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class Profile(BaseModel):
    name: str
    dob: str  # YYYY-MM-DD
    tob: str | None = None
    pob: str | None = None


class Expect(BaseModel):
    sun_sign: str | None = None  # if set, answer must reference this sign correctly
    must_mention: list[str] = Field(default_factory=list)  # all required
    must_not_contain: list[str] = Field(default_factory=list)  # none allowed
    any_of: list[str] = Field(default_factory=list)  # at least one required
    max_words: int = 250


class Case(BaseModel):
    id: str
    category: Literal["golden", "safety"]
    tags: list[str]
    persona: Literal["vedic", "western", "love"] = "western"
    profile: Profile
    question: str
    expect: Expect


def load_cases(path: str | Path) -> list[Case]:
    cases: list[Case] = []
    for n, line in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            cases.append(Case.model_validate_json(line))
        except Exception as exc:
            raise ValueError(f"{path}:{n}: {exc}") from exc
    ids = [c.id for c in cases]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        raise ValueError(f"{path}: duplicate ids {sorted(dupes)}")
    return cases
