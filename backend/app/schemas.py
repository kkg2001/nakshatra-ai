from __future__ import annotations

import re
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class Profile(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    dob: str
    tob: str | None = None
    pob: str | None = Field(default=None, max_length=80)

    @field_validator("dob")
    @classmethod
    def _dob(cls, v: str) -> str:
        d = date.fromisoformat(v)  # raises ValueError -> 422
        if d.year < 1900 or d > date.today():
            raise ValueError("dob must be between 1900 and today")
        return v

    @field_validator("tob")
    @classmethod
    def _tob(cls, v: str | None) -> str | None:
        if v in (None, ""):
            return None
        if not re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v):
            raise ValueError("tob must be HH:MM")
        return v


class Turn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=2000)


class ChatRequest(BaseModel):
    profile: Profile
    question: str = Field(min_length=1, max_length=500)
    persona: Literal["vedic", "western", "love"] = "western"
    history: list[Turn] = Field(default_factory=list, max_length=10)
