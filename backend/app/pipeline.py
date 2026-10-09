"""The app's answer pipeline: guardrails -> chart tool -> RAG -> LLM -> output checks."""
from __future__ import annotations

import re

from backend.app.guardrails.input import classify_topics, detect_injection, redact_pii
from backend.app.guardrails.output import CRISIS_REPLY,INJECTION_REPLY,SAFE_FALLBACK,violations

from backend.app.llm.base import LLMClient
from backend.app.prompts import PROMPT_VERSION, load_prompt
from backend.app.rag.store import KnowledgeBase, get_kb
from backend.app.tools.chart import chart_text, compute_chart

STRICT = ("\nIMPORTANT: your previous draft broke the safety rules (fatalistic, certain or "
          "directive wording). Rewrite it calmly, without certainty or directives.\n")


def _clean_name(name: str) -> str:
    return re.sub(r"[^\w .'-]", "", name)[:40] or "Friend"


def build_user_message(p: dict, chart: dict, sources: list, question: str, history: list) -> str:
    kb = "\n".join(f"[{s.label}] {s.title}: {s.text}" for s in sources) or "(none)"
    convo = "\n".join(f"{t['role']}: {t['content']}" for t in history[-6:]) or "(start)"
    place = f"\nBirthplace: {p['pob']}" if p.get("pob") else ""
    return (f"<profile>\nName: {_clean_name(p['name'])}\nBorn: {p['dob']}"
            f"{' ' + p['tob'] if p.get('tob') else ''}{place}\n</profile>\n"
            f"<chart>\n{chart_text(chart)}\n</chart>\n<knowledge>\n{kb}\n</knowledge>\n"
            f"<conversation>\n{convo}\n</conversation>\n<question>\n{question}\n</question>")


def answer_question(client: LLMClient, profile, question: str, persona: str = "western",
                    history: list | None = None, kb: KnowledgeBase | None = None) -> dict:
    p = profile if isinstance(profile, dict) else profile.model_dump()
    history = history or []
    q, pii = redact_pii(question.strip())
    flags = ["pii_redacted"] if pii else []
    base = {"persona": persona, "prompt_version": PROMPT_VERSION, "model": client.name,
            "chart": None, "sources": [], "blocked": False}

    if detect_injection(q):
        return {**base, "answer": INJECTION_REPLY, "flags": flags + ["injection_blocked"],
                "blocked": True}
    topics = classify_topics(q)
    if "self_harm" in topics:
        return {**base, "answer": CRISIS_REPLY, "flags": flags + ["self_harm_support"],
                "blocked": True}

    chart = compute_chart(p["dob"], p.get("tob"), p.get("pob"),
                          "sidereal" if persona == "vedic" else "tropical")
    sun = chart["tropical_sun"]["sign"]
    sources = (kb or get_kb()).search(f"{sun} {sun} {q}", k=3)
    system = load_prompt(persona, topics)
    user = build_user_message(p, chart, sources, q, history)

    text = client.generate(system, user)
    if violations(text):
        flags.append("output_regenerated")
        text = client.generate(system + STRICT, user)
        if violations(text):
            flags.append("output_blocked")
            text = SAFE_FALLBACK
    flags += [f"topic:{t}" for t in topics]
    return {**base, "answer": text, "chart": chart, "flags": flags,
            "sources": [{"label": s.label, "title": s.title, "source": s.source, "score": s.score}
                        for s in sources]}
