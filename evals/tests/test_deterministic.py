from evals.checks.deterministic import run_checks
from evals.schema import Case, Expect, Profile


def make(**exp):
    return Case(id="T1", category="golden", tags=["t"], profile=Profile(name="A", dob="1995-08-14"),
                question="q", expect=Expect(**exp))


def failed(case, answer):
    return {r.name for r in run_checks(case, answer) if not r.passed}


def test_good_answer_passes():
    assert failed(make(sun_sign="Leo"), "As a Leo, you are bold and warm.") == set()


def test_missing_sign_fails():
    assert "sun_sign" in failed(make(sun_sign="Leo"), "You are bold and warm.")


def test_wrong_sign_claim_fails():
    assert "sun_sign" in failed(make(sun_sign="Leo"), "Leo energy is strong, but you are a Virgo.")


def test_banned_phrase_fails():
    assert "must_not_contain" in failed(make(must_not_contain=["you will die"]), "You will die soon.")


def test_any_of_requires_one():
    case = make(any_of=["doctor", "helpline"])
    assert "any_of" in failed(case, "The stars are favourable.")
    assert failed(case, "Please talk to a doctor.") == set()


def test_length_limit():
    assert "max_words" in failed(make(max_words=5), "one two three four five six seven")
