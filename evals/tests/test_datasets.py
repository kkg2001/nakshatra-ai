from pathlib import Path

from evals.checks.zodiac import sun_sign
from evals.schema import load_cases

DATA = Path(__file__).parents[1] / "datasets"


def test_golden_loads_and_labels_match_oracle():
    cases = load_cases(DATA / "golden.jsonl")
    assert len(cases) >= 12
    for c in cases:
        assert c.expect.sun_sign == sun_sign(c.profile.dob), c.id


def test_safety_cases_have_a_pass_condition():
    cases = load_cases(DATA / "safety.jsonl")
    assert len(cases) >= 8
    for c in cases:
        assert c.expect.must_not_contain or c.expect.any_of, c.id
