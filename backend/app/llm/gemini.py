from __future__ import annotations

import os
import time

from backend.app.llm.base import LLMError


class GeminiClient:
    def __init__(self, model: str | None = None, min_interval: float = 5.0, retries: int = 4):
        from google import genai  # imported lazily so tests don't need the package

        key = os.getenv("GEMINI_API_KEY")
        if not key:
            raise LLMError("GEMINI_API_KEY is not set (copy .env.example to .env)")
        self._client = genai.Client(api_key=key)
        self.model = model or os.getenv("GEMINI_MODEL", "gemini-3.8-flash-lite")
        self.name = f"gemini:{self.model}"
        self._min_interval = min_interval
        self._retries = retries
        self._last = 0.0

    def generate(self, system: str, user: str, temperature: float | None = None) -> str:
        from google.genai import types

        cfg = types.GenerateContentConfig(
            system_instruction=system, temperature=0.7 if temperature is None else temperature,
            max_output_tokens=1024
        )
        last_exc: Exception | None = None
        for attempt in range(self._retries):
            wait = self._min_interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                resp = self._client.models.generate_content(
                    model=self.model, contents=user, config=cfg
                )
                return (resp.text or "").strip()
            except Exception as exc:  # rate limits, 5xx, network
                last_exc = exc
                if getattr(exc, "code", None) == 429 or "RESOURCE_EXHAUSTED" in str(exc):
                    break
                time.sleep(min(2 ** attempt * 5, 60))
        raise LLMError(f"Gemini failed after {self._retries} attempts: {last_exc}")
