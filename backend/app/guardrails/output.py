from __future__ import annotations

import re

BANNED = [
    r"\byou will (die|pass away) (on|in|at|by|before|after)\b",
    r"100% certain",
    r"\byou are (indeed |truly )?cursed\b",
    r"\bthe curse is real\b",
    r"\b(you should|go ahead and|you can) (stop|skip) (your |taking |the )?"
    r"(chemo|chemotherapy|treatment|medication|prenatal|checkups?)\b",
    r"\bgo all in\b",
]


def violations(text: str) -> list[str]:
    return [p for p in BANNED if re.search(p, text, re.IGNORECASE)]


INJECTION_REPLY = ("I can't share or change my internal setup, but I'm glad to help with "
                   "astrology questions about your sign, chart, relationships or career. "
                   "What would you like to explore?")
CRISIS_REPLY = (
    "I'm really sorry you're feeling this way, and I'm glad you said it out loud. This is "
    "beyond what astrology can help with, and you deserve real support. Please reach out to "
    "someone you trust today, or contact a crisis line. In India, Tele-MANAS (14416) offers "
    "free 24x7 support; in the US you can call or text 988. If you might act on these feelings "
    "or are in immediate danger, please contact local emergency services now. I'm here to "
    "keep talking if that helps."
)
SAFE_FALLBACK = ("I'd rather not answer that in a way that could mislead you. Astrology offers "
                 "themes for reflection, not certainties, and your choices matter far more. "
                 "Could you tell me more about what you're hoping to understand?")
