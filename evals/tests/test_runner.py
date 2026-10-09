from backend.app.llm.mock import MockClient
from evals.baseline import baseline_answer, build_user_message
from evals.runner import run_cases, summarize
from evals.schema import Case, Expect, Profile


def make(i, cat="golden", **exp):
    return Case(id=i, category=cat, tags=["t"], profile=Profile(name="Asha", dob="1995-08-14"),
                question="q", expect=Expect(**exp))


def test_all_pass_with_good_answer():
    cases = [make("A", sun_sign="Leo"), make("B", sun_sign="Leo")]
    res = run_cases(cases, lambda c: "As a Leo, you shine.")
    assert summarize(res)["overall"]["pass_rate"] == 1.0


def test_failures_are_reported_per_case():
    cases = [make("A", sun_sign="Leo"), make("B", "safety", any_of=["doctor"])]
    res = run_cases(cases, lambda c: "Leo is bold.")
    assert [r["passed"] for r in res] == [True, False]
    s = summarize(res)
    assert s["safety"]["pass_rate"] == 0.0 and s["golden"]["pass_rate"] == 1.0


def test_llm_error_counts_as_failure_not_crash():
    def boom(case):
        raise RuntimeError("quota")
    res = run_cases([make("A")], boom)
    assert res[0]["passed"] is False and "quota" in res[0]["error"]


def test_baseline_uses_client_and_includes_profile():
    seen = {}
    client = MockClient(lambda s, u: seen.update(system=s, user=u) or "ok")
    assert baseline_answer(client, make("A")) == "ok"
    assert "1995-08-14" in seen["user"] and "astrologer" in seen["system"]
    assert "Asha" in build_user_message(make("A"))
