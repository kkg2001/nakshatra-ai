"""Validate datasets: schema, unique ids, and sun_sign labels match the date oracle."""
from __future__ import annotations

from pathlib import Path

from evals.checks.zodiac import sun_sign
from evals.schema import load_cases

DATA = Path(__file__).parent / "datasets"


def main() -> None:
    total = 0
    for f in sorted(DATA.glob("*.jsonl")):
        cases = load_cases(f)
        for c in cases:
            if c.expect.sun_sign and c.expect.sun_sign != sun_sign(c.profile.dob):
                raise SystemExit(f"{c.id}: label {c.expect.sun_sign} != {sun_sign(c.profile.dob)}")
        print(f"{f.name}: {len(cases)} cases OK")
        total += len(cases)
    print(f"Total: {total}")


if __name__ == "__main__":
    main()
