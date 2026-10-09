from __future__ import annotations

import logging
import os
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.app.config import FRONTEND_DIR
from backend.app.llm.base import LLMClient, LLMError
from backend.app.llm.factory import make_llm
from backend.app.pipeline import answer_question
from backend.app.schemas import ChatRequest, Profile
from backend.app.tools.chart import compute_chart

log = logging.getLogger("nakshatra")
app = FastAPI(title="Nakshatra")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

_hits: dict[str, deque] = defaultdict(deque)


def rate_limit(request: Request) -> None:
    """Protects free-tier quota: N requests per minute per IP (RATE_LIMIT_PER_MIN)."""
    limit = int(os.getenv("RATE_LIMIT_PER_MIN", "20"))
    q, now = _hits[request.client.host if request.client else "?"], time.time()
    while q and now - q[0] > 60:
        q.popleft()
    if len(q) >= limit:
        raise HTTPException(429, "Too many requests. Please wait a minute.")
    q.append(now)


@lru_cache(maxsize=1)
def _client() -> LLMClient:
    return make_llm()


def get_client() -> LLMClient:
    try:
        return _client()
    except LLMError as exc:
        raise HTTPException(503, str(exc)) from exc


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/chat", dependencies=[Depends(rate_limit)])
def chat(req: ChatRequest, client: LLMClient = Depends(get_client)):
    try:
        return answer_question(client, req.profile, req.question, req.persona,
                               [t.model_dump() for t in req.history])
    except LLMError as exc:
        log.error("LLM failure: %s", exc)
        raise HTTPException(
            503, "The astrologer is unavailable right now. Please try again shortly.") from exc


@app.post("/api/chart")
def chart(profile: Profile, persona: str = "western"):
    return compute_chart(profile.dob, profile.tob, profile.pob,
                         "sidereal" if persona == "vedic" else "tropical")


if FRONTEND_DIR.exists():
    app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="web")
