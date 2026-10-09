from __future__ import annotations

import os

from backend.app.llm.base import LLMClient, LLMError

def make_llm() -> LLMClient:
    """Gemini first, Groq as fallback, depending on which keys are configured."""
    from backend.app.llm.fallback import FallbackClient

    clients: list[LLMClient] = []
    if os.getenv("GEMINI_API_KEY"):
        from backend.app.llm.gemini import GeminiClient
        clients.append(GeminiClient())
    if os.getenv("GROQ_API_KEY"):
        from backend.app.llm.groq import GroqClient
        clients.append(GroqClient())
    if not clients:
        raise LLMError("No LLM configured: set GEMINI_API_KEY and/or GROQ_API_KEY in .env")
    return clients[0] if len(clients) == 1 else FallbackClient(clients)
