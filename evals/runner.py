"""Run eval datasets against a system, score with checks (+ optional judge), write a report.

Examples:
    python -m evals.runner --mock --limit 5                 # offline dry run
    python -m evals.runner --system baseline --judge        # naive baseline (uses quota)
    python -m evals.runner --system app --judge --min-pass-rate 0.8
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from datetime import datetime
from functools import partial
from pathlib import Path

from evals.checks.deterministic import run_checks
from evals.schema import Case, load_cases

DATA = Path(__file__).parent / "datasets"
REPORTS = Path(__file__).parent / "reports"


def run_cases(cases: list[Case], answer_fn: Callable[[Case], str], judge=None) -> list[dict]:
    results = []
    for case in cases:
        start = time.time()
        answer, error = "", None
        try:
            answer = answer_fn(case)
        except Exception as exc:
            error = str(exc)
        checks = run_checks(case, answer) if error is None else []
        failed = [f"{c.name}: {c.detail}" for c in checks if not c.passed]
        verdict = None
        if judge and error is None:
            try:
                verdict = judge(case, answer)
                failed += verdict.failures
            except Exception as exc:
                error = f"judge: {exc}"
        results.append({
            "id": case.id, "category": case.category, "tags": case.tags,
            "passed": error is None and not failed, "failed_checks": failed,
            "error": error, "answer": answer, "latency_s": round(time.time() - start, 2),
            "judge": {"scores": verdict.scores, "reasons": verdict.reasons} if verdict else None,
        })
    return results


def summarize(results: list[dict]) -> dict:
    out: dict = {}
    for cat in sorted({r["category"] for r in results}):
        rs = [r for r in results if r["category"] == cat]
        passed = sum(r["passed"] for r in rs)
        out[cat] = {"cases": len(rs), "passed": passed, "pass_rate": round(passed / len(rs), 3)}
    total, passed = len(results), sum(r["passed"] for r in results)
    out["overall"] = {"cases": total, "passed": passed,
                      "pass_rate": round(passed / total, 3) if total else 0.0}
    return out


def judge_means(results: list[dict]) -> dict:
    rows = [r["judge"]["scores"] for r in results if r.get("judge")]
    if not rows:
        return {}
    return {k: round(sum(r[k] for r in rows) / len(rows), 2) for k in rows[0]}


def print_report(summary: dict, results: list[dict]) -> None:
    print(f"\n{'Category':<10} {'Cases':>6} {'Passed':>7} {'Rate':>7}")
    for cat, s in summary.items():
        print(f"{cat:<10} {s['cases']:>6} {s['passed']:>7} {s['pass_rate']:>7.0%}")
    means = judge_means(results)
    if means:
        print("\nJudge mean scores (1-5): " + ", ".join(f"{k}={v}" for k, v in means.items()))
    bad = [r for r in results if not r["passed"]]
    if bad:
        print("\nFailures:")
        for r in bad:
            print(f"  {r['id']}: {r['error'] or '; '.join(r['failed_checks'])}")


def save_report(system: str, meta: dict, summary: dict, results: list[dict]) -> Path:
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / f"{system}-{datetime.now():%Y%m%d-%H%M%S}.json"
    path.write_text(json.dumps({"system": system, **meta, "summary": summary,
                                "judge_means": judge_means(results), "results": results},
                               indent=2), encoding="utf-8")
    return path


def build_client(provider: str, model: str | None = None):
    if provider == "mock":
        from backend.app.llm.mock import MockClient
        return MockClient()
    if provider == "groq":
        from backend.app.llm.groq import GroqClient
        return GroqClient(model=model)
    if provider == "auto":
        from backend.app.llm.factory import make_llm
        return make_llm()
    from backend.app.llm.gemini import GeminiClient
    return GeminiClient(model=model)


def main() -> None:
    from dotenv import load_dotenv

    ap = argparse.ArgumentParser()
    ap.add_argument("--system", choices=["baseline", "app"], default="baseline")
    ap.add_argument("--provider", choices=["gemini", "groq", "auto"], default="gemini")
    ap.add_argument("--mock", action="store_true", help="offline mock client (no quota)")
    ap.add_argument("--judge", action="store_true", help="also score with LLM-as-judge")
    ap.add_argument("--limit", type=int, default=None, help="only run first N cases")
    ap.add_argument("--min-pass-rate", type=float, default=None, help="exit 1 if overall is lower")
    args = ap.parse_args()
    load_dotenv()

    provider = "mock" if args.mock else args.provider
    client = build_client(provider)
    judge, judge_name = None, ""
    if args.judge:
        from evals.checks.judge import Judge
        if args.mock:
            from backend.app.llm.mock import MockClient
            jc = MockClient('{"scores":{"tone":4,"specificity":4,"safety_responsibility":4,'
                            '"persona_consistency":4},"reasons":{}}')
        else:
            jc = build_client(provider, os.getenv("JUDGE_MODEL") or None)
        judge, judge_name = Judge(jc), jc.name

    if args.system == "app":
        from evals.app_system import app_answer
        answer_fn = partial(app_answer, client)
    else:
        from evals.baseline import baseline_answer
        answer_fn = partial(baseline_answer, client)

    cases = load_cases(DATA / "golden.jsonl") + load_cases(DATA / "safety.jsonl")
    if args.limit:
        cases = cases[: args.limit]
    print(f"Running {len(cases)} cases on {args.system} / {client.name} ...")
    results = run_cases(cases, answer_fn, judge)
    summary = summarize(results)
    print_report(summary, results)

    meta = {"model": client.name, "judge_model": judge_name}
    if args.system == "app":
        from backend.app.prompts import PROMPT_VERSION
        meta["prompt_version"] = PROMPT_VERSION
    print(f"\nSaved: {save_report(args.system, meta, summary, results)}")
    if args.min_pass_rate is not None and summary["overall"]["pass_rate"] < args.min_pass_rate:
        print(f"FAIL: overall pass rate below {args.min_pass_rate:.0%}")
        sys.exit(1)


if __name__ == "__main__":
    main()
