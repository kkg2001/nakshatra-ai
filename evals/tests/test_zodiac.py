import pytest

from evals.checks.zodiac import sun_sign


@pytest.mark.parametrize("dob,expected", [
    ("1995-08-14", "Leo"), ("1980-01-05", "Capricorn"), ("2000-03-05", "Pisces"),
    ("1993-12-10", "Sagittarius"), ("1990-12-30", "Capricorn"), ("1996-02-08", "Aquarius"),
])
def test_sun_sign(dob, expected):
    assert sun_sign(dob) == expected
