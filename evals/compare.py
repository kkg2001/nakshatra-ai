"""Print the latest baseline vs app reports side by side (the before/after table)."""
from __future__ import annotations

import json
from pathlib import Path

REPORTS = Path(__file__).parent / "reports"


def latest(system: str) -> dict | None:
    files = sorted(REPORTS.glob(f"{system}-*.json"))
    return json.loads(files[-1].read_text(encoding="utf-8")) if files else None


def main() -> None:
    base, app = latest("baseline"), latest("app")
    if not base or not app:
        raise SystemExit("Need at least one baseline and one app report in evals/reports/")
    print(f"{'Metric':<28}{'Baseline':>10}{'App':>10}")
    for cat in ("golden", "safety", "overall"):
        b, a = base["summary"].get(cat), app["summary"].get(cat)
        if b and a:
            print(f"{cat + ' pass rate':<28}{b['pass_rate']:>10.0%}{a['pass_rate']:>10.0%}")
    for k in base.get("judge_means", {}):
        a = app.get("judge_means", {}).get(k)
        if a is not None:
            print(f"{'judge ' + k:<28}{base['judge_means'][k]:>10}{a:>10}")
    print(f"\nBaseline model: {base.get('model')}   App model: {app.get('model')}"
          f"   Prompt: {app.get('prompt_version')}")


if __name__ == "__main__":
    main()
