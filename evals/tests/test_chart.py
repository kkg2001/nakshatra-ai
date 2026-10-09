from pathlib import Path

import pytest

from backend.app.tools.chart import chart_text, compute_chart, find_city
from evals.checks.zodiac import sun_sign
from evals.schema import load_cases

swe = pytest.importorskip("swisseph")
DATA = Path(__file__).parents[1] / "datasets"


def test_tool_sun_sign_matches_independent_oracle():
    for c in load_cases(DATA / "golden.jsonl"):
        assert compute_chart(c.profile.dob)["tropical_sun"]["sign"] == sun_sign(c.profile.dob), c.id


def test_known_position_j2000():
    jd = swe.julday(2000, 1, 1, 12.0)
    lon = swe.calc_ut(jd, swe.SUN, swe.FLG_MOSEPH)[0][0]
    assert 280.0 < lon < 280.7  # Sun at ~10 deg Capricorn on J2000


def test_sidereal_sun_is_about_24_degrees_behind():
    t = compute_chart("1990-11-05", system="tropical")["sun"]
    s = compute_chart("1990-11-05", system="sidereal")["sun"]
    assert (t["sign"], s["sign"]) == ("Scorpio", "Libra")


def test_nakshatra_present_for_sidereal_only():
    s = compute_chart("1990-11-05", "10:30", "Bengaluru", "sidereal")
    assert s["nakshatra"]["name"] and 1 <= s["nakshatra"]["pada"] <= 4
    assert compute_chart("1990-11-05", "10:30", "Bengaluru")["nakshatra"] is None


def test_rising_needs_time_and_known_city():
    assert compute_chart("1995-08-14", "08:15", "Mumbai")["rising"] is not None
    assert compute_chart("1995-08-14", None, "Mumbai")["rising"] is None
    assert compute_chart("1995-08-14", "08:15", "Atlantis")["rising"] is None


def test_unknown_time_flags_approximate_moon():
    c = compute_chart("1995-08-14")
    assert c["moon_approximate"] and "approximate" in chart_text(c)


def test_find_city():
    assert find_city("Bengaluru, India")[2] == "Asia/Kolkata"
    assert find_city("nowhere") is None
