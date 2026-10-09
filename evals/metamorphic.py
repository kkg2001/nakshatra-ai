"""Metamorphic tests: harmless input changes must not change pass/fail behaviour.

Variants: different name, polite prefix, upper-cased question. A case is 'consistent' if the
original and all variants give the same deterministic verdict."""
from __future__ import annotations

import argparse
from collections.abc import Callable
from functools import partial

from evals.checks.deterministic import run_checks
from evals.schema import Case

VARIANTS: dict[str, Callable[[Case], Case]] = {
    "renamed": lambda c: c.model_copy(update={"profile": c.profile.model_copy(update={"name": "Sam"})}),
    "polite": lambda c: c.model_copy(update={"question": "Quick question, please: " + c.question}),
    "uppercase": lambda c: c.model_copy(update={"question": c.question.upper()}),
}


def passes(case: Case, answer: str) -> bool:
    return all(r.passed for r in run_checks(case, answer))


def run_metamorphic(cases: list[Case], answer_fn: Callable[[Case], str]) -> dict:
    rows = []
    for case in cases:
        verdicts = {"original": passes(case, answer_fn(case))}
        for name, make in VARIANTS.items():
            verdicts[name] = passes(case, answer_fn(make(case)))
        rows.append({"id": case.id, "verdicts": verdicts,
                     "consistent": len(set(verdicts.values())) == 1})
    n = len(rows)
    return {"cases": n, "consistency": round(sum(r["consistent"] for r in rows) / n, 3) if n else 0,
            "inconsistent": [r for r in rows if not r["consistent"]]}


def main() -> None:
    from dotenv import load_dotenv

    from evals.app_system import app_answer
    from evals.runner import DATA, build_client
    from evals.schema import load_cases

    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=6)
    ap.add_argument("--provider", choices=["gemini", "groq", "auto"], default="gemini")
    ap.add_argument("--mock", action="store_true")
    args = ap.parse_args()
    load_dotenv()
    client = build_client("mock" if args.mock else args.provider)
    cases = (load_cases(DATA / "golden.jsonl") + load_cases(DATA / "safety.jsonl"))[: args.limit]
    print(f"{len(cases)} cases x {1 + len(VARIANTS)} runs each on {client.name} ...")
    out = run_metamorphic(cases, partial(app_answer, client))
    print(f"Consistency: {out['consistency']:.0%}")
    for r in out["inconsistent"]:
        print(f"  {r['id']}: {r['verdicts']}")


if __name__ == "__main__":
    main()
