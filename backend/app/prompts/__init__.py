from pathlib import Path

PROMPT_VERSION = "v1"
_DIR = Path(__file__).parent

DIRECTIVES = {
    "medical": "The user raised a health matter. Say clearly you are not a medical professional, "
               "do NOT advise starting, stopping or skipping any treatment or checkup, and "
               "encourage consulting their doctor.",
    "legal": "The user raised a legal matter. Say you are not a lawyer, do not predict the "
             "outcome, and encourage speaking to a qualified lawyer.",
    "financial": "The user raised a money matter. Say you are not a financial advisor, give no "
                 "advice on specific investments, promise no outcomes, and recommend a "
                 "qualified financial advisor.",
    "death": "The user asked about death or lifespan. State plainly that astrology cannot "
             "predict death and that no one can. Never imply when someone will die. Offer a "
             "gentle, supportive reframing.",
}

def load_prompt(persona: str, topics: list[str] | None = None) -> str:
    text = (_DIR / "base.md").read_text(encoding="utf-8")
    text += (_DIR / f"{persona}.md").read_text(encoding="utf-8")
    extra = [DIRECTIVES[t] for t in (topics or []) if t in DIRECTIVES]
    if extra:
        text += "\nSENSITIVE-TOPIC RULES FOR THIS ANSWER\n" + "\n".join(f"- {e}" for e in extra) + "\n"
    return text