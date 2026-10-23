from __future__ import annotations

import os
import re
import time

from backend.app.llm.base import LLMError


def trim_to_sentence(text: str) -> str:
    t = text.rstrip()
    ends = list(re.finditer(r"[.!?][\"')\]*]*(?=\s|$)", t))
    if not ends or ends[-1].end() == len(t):
        return t
    return t[: ends[-1].end()].rstrip()


def _truncated(resp) -> bool:
    try:
        return "MAX_TOKENS" in str(resp.candidates[0].finish_reason).upper()
    except Exception:
        return False


def thinking_config(model: str):
    from google.genai import types

    level = (os.getenv("GEMINI_THINKING_LEVEL") or "").strip()
    try:
        if level.lower() == "default":
            return None
        if level:
            return types.ThinkingConfig(thinking_level=level.upper())
        m = model.lower()
        if "2.5" in m:
            return types.ThinkingConfig(thinking_budget=128 if "pro" in m else 0)
        return types.ThinkingConfig(thinking_level="LOW")
    except Exception:
        return None  # older SDK without these fields


class GeminiClient:
    def __init__(self, model: str | None = None, min_interval: float | None = None,
                 retries: int = 4):
        from google import genai  # imported lazily so tests don't need the package

        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY is not set (copy .env.example to .env)")
        self._client = genai.Client(api_key=key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        self.name = f"gemini:{self.model}"
        self._min_interval = (float(os.getenv("GEMINI_MIN_INTERVAL", "0"))
                              if min_interval is None else min_interval)
        self._retries = retries
        self._max_tokens = int(os.getenv("GEMINI_MAX_OUTPUT_TOKENS", "4096"))
        self._ceiling = max(self._max_tokens, 16384)
        self._last = 0.0

    def _pace(self) -> None:
        wait = self._min_interval - (time.time() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.time()

    def generate(self, system: str, user: str, temperature: float | None = None) -> str:
        from google.genai import types

        temp = 0.7 if temperature is None else temperature
        max_tokens, thinking = self._max_tokens, thinking_config(self.model)
        last: Exception | str | None = None
        for attempt in range(self._retries):
            self._pace()
            cfg = {"system_instruction": system, "temperature": temp,
                   "max_output_tokens": max_tokens}
            if thinking is not None:
                cfg["thinking_config"] = thinking
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=user,
                    config=types.GenerateContentConfig(**cfg))
            except Exception as exc:  # rate limits, 5xx, network, bad config
                last = exc
                if thinking is not None and "thinking" in str(exc).lower():
                    thinking = None  # this model rejects the setting: retry without it
                    continue
                if getattr(exc, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(exc):
                    break  # quota used up: retrying only burns more, so fail fast
                time.sleep(min(2 ** attempt * 5, 60))
                continue
            text = (getattr(resp, "text", None) or "").strip()
            if text and not _truncated(resp):
                return text
            if max_tokens < self._ceiling:  # cut off or empty: retry with more room
                max_tokens = min(max_tokens * 2, self._ceiling)
                last = "reply was cut off or empty"
                continue
            if text:
                return trim_to_sentence(text)  # never show half a sentence
            last = "empty reply"
        raise LLMError(f"Gemini failed after {self._retries} attempts: {last}")