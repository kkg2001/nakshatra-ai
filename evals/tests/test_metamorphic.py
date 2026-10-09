from evals.metamorphic import run_metamorphic
from evals.schema import Case, Expect, Profile


def case():
    return Case(id="M1", category="golden", tags=["t"], profile=Profile(name="Asha", dob="1995-08-14"),
                question="traits?", expect=Expect(sun_sign="Leo"))


def test_stable_system_is_consistent():
    out = run_metamorphic([case()], lambda c: "As a Leo, you shine.")
    assert out["consistency"] == 1.0


def test_brittle_system_is_flagged():
    # fails whenever the question is upper-cased -> inconsistent
    out = run_metamorphic([case()], lambda c: "Leo!" if c.question.islower() or "?" in c.question and not c.question.isupper() else "hi")
    assert out["consistency"] == 0.0 and out["inconsistent"][0]["id"] == "M1"
