# ---------------------------------------------------------------------------
# Pinterest careers site adapter — pinterestcareers.com/jobs/<id>/<slug>/
# Custom wrapper around Greenhouse. Page structure:
#   main > ... > first <li> = "San Francisco / Palo Alto / Seattle" (location)
#              > second <li> = team, third <li> = employment type
#   h1 = job title (generic handles this)
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "pinterestcareers.com"


def _pinterest_location(doc: BeautifulSoup, url: str) -> str | None:
    # First <li> in main contains the location string
    for li in doc.select("main li"):
        t = _text(li)
        if t and t not in ("", "Regular", "Temporary"):
            return t
    return None


def _pinterest_role_type(doc: BeautifulSoup, url: str) -> str | None:
    # Third <li> in main is employment type: "Regular" → full-time, "Temporary" → contract
    lis = [li for li in doc.select("main li") if _text(li)]
    if len(lis) >= 3:
        raw = (_text(lis[2]) or "").lower()
        if "regular" in raw:
            return "full-time"
        if "temporary" in raw:
            return "contract"
        if "intern" in raw:
            return "internship"
    return None


def _pinterest_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Pinterest",
    "location": _pinterest_location,
    "role_type": _pinterest_role_type,
    "description": _pinterest_description,
}
