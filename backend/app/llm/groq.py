from __future__ import annotations

import os
import time

import httpx

from backend.app.llm.base import LLMError

URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqClient:
    def __init__(self, model: str | None = None, retries: int = 3, min_interval: float = 2.0):
        self._key = os.getenv("GROQ_API_KEY")
        if not self._key:
            raise LLMError("GROQ_API_KEY is not set")
        self.model = model or os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
        self.name = f"groq:{self.model}"
        self._retries, self._min_interval, self._last = retries, min_interval, 0.0

    def generate(self, system: str, user: str, temperature: float | None = None) -> str:
        body = {
            "model": self.model,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
            "temperature": 0.7 if temperature is None else temperature,
            "max_tokens": 1024,
        }
        last: Exception | str | None = None
        for attempt in range(self._retries):
            wait = self._min_interval - (time.time() - self._last)
            if wait > 0:
                time.sleep(wait)
            self._last = time.time()
            try:
                r = httpx.post(URL, json=body, timeout=60,
                               headers={"Authorization": f"Bearer {self._key}"})
                if r.status_code == 200:
                    return r.json()["choices"][0]["message"]["content"].strip()
                last = f"HTTP {r.status_code}"
                if r.status_code not in (429, 500, 502, 503):
                    break
            except Exception as exc:
                last = exc
            time.sleep(min(2 ** attempt * 3, 30))
        raise LLMError(f"Groq failed: {last}")
