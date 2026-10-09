"""Chart tool: real planetary positions via Swiss Ephemeris (built-in Moshier data, no files).

The LLM never guesses positions; it only interprets what this tool computes."""
from __future__ import annotations

from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

try:
    import swisseph as swe
except ImportError:  # graceful degradation: sun sign only
    swe = None

SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", "Libra", "Scorpio",
         "Sagittarius", "Capricorn", "Aquarius", "Pisces"]
NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
    "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
    "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
DEFAULT_TZ = "Asia/Kolkata"
# city -> (lat, lon, IANA timezone). Small built-in table so no geocoding API is needed.
CITIES = {
    "bengaluru": (12.97, 77.59, "Asia/Kolkata"), "bangalore": (12.97, 77.59, "Asia/Kolkata"),
    "mumbai": (19.08, 72.88, "Asia/Kolkata"), "delhi": (28.61, 77.21, "Asia/Kolkata"),
    "chennai": (13.08, 80.27, "Asia/Kolkata"), "kolkata": (22.57, 88.36, "Asia/Kolkata"),
    "hyderabad": (17.38, 78.48, "Asia/Kolkata"), "pune": (18.52, 73.86, "Asia/Kolkata"),
    "ahmedabad": (23.02, 72.57, "Asia/Kolkata"), "jaipur": (26.91, 75.79, "Asia/Kolkata"),
    "lucknow": (26.85, 80.95, "Asia/Kolkata"), "kochi": (9.93, 76.27, "Asia/Kolkata"),
    "london": (51.51, -0.13, "Europe/London"), "new york": (40.71, -74.01, "America/New_York"),
    "san francisco": (37.77, -122.42, "America/Los_Angeles"),
    "singapore": (1.35, 103.82, "Asia/Singapore"), "dubai": (25.20, 55.27, "Asia/Dubai"),
    "sydney": (-33.87, 151.21, "Australia/Sydney"), "toronto": (43.65, -79.38, "America/Toronto"),
}
_FALLBACK_STARTS = [(1, 1, 9), (1, 20, 10), (2, 19, 11), (3, 21, 0), (4, 20, 1), (5, 21, 2),
                    (6, 21, 3), (7, 23, 4), (8, 23, 5), (9, 23, 6), (10, 23, 7), (11, 22, 8),
                    (12, 22, 9)]


def find_city(place: str | None):
    if not place:
        return None
    p = place.lower()
    return next((v for k, v in CITIES.items() if k in p), None)


def _pos(lon: float) -> dict:
    return {"sign": SIGNS[int(lon // 30) % 12], "degree": round(lon % 30, 1)}


def _to_jd(dob: str, tob: str | None, tz: str) -> float:
    local = datetime.fromisoformat(f"{dob}T{tob or '12:00'}").replace(tzinfo=ZoneInfo(tz))
    ut = local.astimezone(timezone.utc)
    return swe.julday(ut.year, ut.month, ut.day, ut.hour + ut.minute / 60)


def _fallback_sun(dob: str) -> dict:
    d = date.fromisoformat(dob)
    idx = 9
    for m, day, i in _FALLBACK_STARTS:
        if (d.month, d.day) >= (m, day):
            idx = i
    return {"sign": SIGNS[idx], "degree": None}


def compute_chart(dob: str, tob: str | None = None, place: str | None = None,
                  system: str = "tropical") -> dict:
    notes: list[str] = []
    if swe is None:
        sun = _fallback_sun(dob)
        return {"system": "tropical", "tropical_sun": sun, "sun": sun, "moon": None,
                "rising": None, "nakshatra": None, "moon_approximate": True, "timezone": None,
                "notes": ["Ephemeris library unavailable: only the sun sign is known."]}

    city = find_city(place)
    tz = city[2] if city else DEFAULT_TZ
    if not city:
        notes.append(f"Birthplace not recognised; assumed timezone {DEFAULT_TZ}.")
    if not tob:
        notes.append("Birth time unknown: Moon position is approximate and no rising sign is given.")
    jd = _to_jd(dob, tob, tz)

    def lon(body: int, sidereal: bool) -> float:
        flags = swe.FLG_MOSEPH | (swe.FLG_SIDEREAL if sidereal else 0)
        if sidereal:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        return swe.calc_ut(jd, body, flags)[0][0]

    sidereal = system == "sidereal"
    sun, moon = lon(swe.SUN, sidereal), lon(swe.MOON, sidereal)
    rising = None
    if tob and city:
        if sidereal:
            swe.set_sid_mode(swe.SIDM_LAHIRI)
        asc = swe.houses_ex(jd, city[0], city[1], b"W", swe.FLG_SIDEREAL if sidereal else 0)[1][0]
        rising = _pos(asc)
    elif tob:
        notes.append("Rising sign needs a recognised birthplace.")

    nak = None
    if sidereal:
        span = 360 / 27
        nak = {"name": NAKSHATRAS[int(moon // span) % 27], "pada": int((moon % span) // (span / 4)) + 1}
    return {"system": system, "tropical_sun": _pos(lon(swe.SUN, False)), "sun": _pos(sun),
            "moon": _pos(moon), "rising": rising, "nakshatra": nak,
            "moon_approximate": not tob, "timezone": tz, "notes": notes}


def chart_text(c: dict) -> str:
    lines = [f"Western (tropical) sun sign: {c['tropical_sun']['sign']}"]
    if c["system"] == "sidereal" and c["moon"]:
        lines.append(f"Vedic (sidereal, Lahiri) Sun rashi: {c['sun']['sign']}")
    if c["moon"]:
        approx = " (approximate)" if c["moon_approximate"] else ""
        label = "Vedic Moon rashi" if c["system"] == "sidereal" else "Moon sign"
        lines.append(f"{label}: {c['moon']['sign']}{approx}")
    if c.get("nakshatra"):
        lines.append(f"Moon nakshatra: {c['nakshatra']['name']} pada {c['nakshatra']['pada']}")
    lines.append(f"Rising sign / lagna: {c['rising']['sign']}" if c["rising"]
                 else "Rising sign / lagna: unknown (birth time or place missing)")
    lines += [f"Note: {n}" for n in c["notes"]]
    return "\n".join(lines)
