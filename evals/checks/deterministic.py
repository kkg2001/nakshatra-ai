"""Fast, free, repeatable checks. These run before any LLM judge."""
from __future__ import annotations

import re
from dataclasses import dataclass

from evals.checks.zodiac import SIGNS
from evals.schema import Case


@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


def _has(text: str, term: str) -> bool:
    return re.search(r"(?<!\w)" + re.escape(term.lower()) + r"(?!\w)", text.lower()) is not None


def check_sun_sign(case: Case, answer: str) -> CheckResult:
    expected = case.expect.sun_sign
    if not expected:
        return CheckResult("sun_sign", True, "n/a")
    if not _has(answer, expected):
        return CheckResult("sun_sign", False, f"does not mention {expected}")
    for other in (s for s in SIGNS if s != expected):
        claim = rf"(you are|you're|your sun sign is|your sign is)\s+(an?\s+)?{other}\b"
        if re.search(claim, answer, re.IGNORECASE):
            return CheckResult("sun_sign", False, f"wrongly claims {other}")
    return CheckResult("sun_sign", True)


def check_must_mention(case: Case, answer: str) -> CheckResult:
    missing = [t for t in case.expect.must_mention if not _has(answer, t)]
    return CheckResult("must_mention", not missing, f"missing: {missing}" if missing else "")


def check_must_not_contain(case: Case, answer: str) -> CheckResult:
    found = [t for t in case.expect.must_not_contain if t.lower() in answer.lower()]
    return CheckResult("must_not_contain", not found, f"found: {found}" if found else "")


def check_any_of(case: Case, answer: str) -> CheckResult:
    opts = case.expect.any_of
    if not opts:
        return CheckResult("any_of", True, "n/a")
    ok = any(o.lower() in answer.lower() for o in opts)
    return CheckResult("any_of", ok, "" if ok else f"none of {opts}")


def check_length(case: Case, answer: str) -> CheckResult:
    words = len(answer.split())
    return CheckResult("max_words", words <= case.expect.max_words, f"{words} words")


def run_checks(case: Case, answer: str) -> list[CheckResult]:
    return [
        check_sun_sign(case, answer),
        check_must_mention(case, answer),
        check_must_not_contain(case, answer),
        check_any_of(case, answer),
        check_length(case, answer),
    ]
