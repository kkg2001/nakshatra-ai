"""Tropical sun sign from a date. Independent oracle for the deterministic checks.
Note: cusp dates (~20th-23rd) vary by year and birth time, so keep test cases off them."""
from __future__ import annotations

from datetime import date

_STARTS = [
    (1, 1, "Capricorn"), (1, 20, "Aquarius"), (2, 19, "Pisces"), (3, 21, "Aries"),
    (4, 20, "Taurus"), (5, 21, "Gemini"), (6, 21, "Cancer"), (7, 23, "Leo"),
    (8, 23, "Virgo"), (9, 23, "Libra"), (10, 23, "Scorpio"), (11, 22, "Sagittarius"),
    (12, 22, "Capricorn"),
]
SIGNS = sorted({s for _, _, s in _STARTS})


def sun_sign(dob: str) -> str:
    d = date.fromisoformat(dob)
    sign = _STARTS[0][2]
    for month, day, name in _STARTS:
        if (d.month, d.day) >= (month, day):
            sign = name
    return sign
