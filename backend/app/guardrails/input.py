from __future__ import annotations

import re

INJECTION = [
    r"ignore (all |any |your )?(previous|prior|above|earlier) (instructions|rules|prompts?)",
    r"(reveal|print|show|repeat|display|leak).{0,40}(system prompt|your instructions|your prompt)",
    r"disregard .{0,30}(instructions|rules)",
    r"you are now (?!going)", r"developer mode", r"\bjailbreak\b", r"act as (?:dan|an? unrestricted)",
]
PII = {
    "email": r"[\w.+-]+@[\w-]+\.[\w.-]+",
    "id_number": r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "phone": r"(?<!\d)\+?\d[\d\s-]{8,13}\d(?!\d)",
}
TOPICS = {
    "self_harm": [r"kill myself", r"suicid", r"want to die", r"end(ing)? it all", r"end my life",
                  r"don'?t want to (live|be here)", r"hurt myself"],
    "medical": [r"cancer", r"chemo", r"pregnan", r"prenatal", r"surgery", r"diagnos", r"medication",
                r"\btreatment\b", r"disease", r"\bsick\b", r"illness", r"therapy"],
    "legal": [r"lawyer", r"attorney", r"custody", r"lawsuit", r"\bcourt\b", r"\bsue\b", r"legal"],
    "financial": [r"invest", r"crypto", r"savings", r"\bstocks?\b", r"\bloan\b", r"trading",
                  r"mortgage", r"lottery"],
    "death": [r"when (will |do )?i (will )?die", r"how (will|do) i die", r"my death",
              r"how long (will )?i (live|have)"],
}


def detect_injection(text: str) -> bool:
    return any(re.search(p, text, re.IGNORECASE) for p in INJECTION)


def redact_pii(text: str) -> tuple[str, list[str]]:
    found = []
    for kind, pat in PII.items():
        if re.search(pat, text):
            found.append(kind)
            text = re.sub(pat, f"[{kind} removed]", text)
    return text, found


def classify_topics(text: str) -> list[str]:
    return [t for t, pats in TOPICS.items() if any(re.search(p, text, re.IGNORECASE) for p in pats)]
