# ---------------------------------------------------------------------------
# Phenom People boards — Yelp (www.yelp.careers), Adobe (careers.adobe.com) and
# Cisco (careers.cisco.com)
# share this ATS template. title and company_name already extract fine via
# the generic adapter (h1 + og:site_name); location and description do not.
# The page renders a duplicate, unfilled "job-description"/".jd-info"
# template block alongside the real one (a Phenom quirk that leaves the
# generic description selector picking up nav/footer/widget cruft instead),
# so description is pulled from the page's own schema.org JobPosting
# JSON-LD block. location isn't a single plain-text element either — the
# JobPosting's jobLocation can be a single Place (Adobe) or a list of them
# for multi-office reqs (Yelp) — so it's parsed from the page <title>'s
# "job in <location> |" segment, which names the specific location this URL
# represents. role_type comes from the JSON-LD employmentType list.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from .._common import _text

HOSTNAMES = ["yelp.careers", "careers.adobe.com", "careers.cisco.com"]


def _phenom_people_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    import json as _json

    for script in doc.find_all("script", type="application/ld+json"):
        if script.get("id"):
            continue
        try:
            d = _json.loads(script.string or "")
        except Exception:
            continue
        if isinstance(d, dict) and "hiringOrganization" in d:
            return d
    return {}


def _phenom_people_location(doc: BeautifulSoup, url: str) -> str | None:
    # The title format varies by tenant: Yelp's is "<title> job in <location> |
    # ...", Adobe's is "<title> in <location> | ..." — so find the last " in "
    # before the pipe rather than anchoring on the word "job".
    title = _text(doc.title)
    if not title:
        return None
    before_pipe = title.split(" | ")[0]
    idx = before_pipe.rfind(" in ")
    if idx == -1:
        return None
    return before_pipe[idx + len(" in ") :].strip() or None


def _phenom_people_description(doc: BeautifulSoup, url: str) -> str | None:
    import html as _html

    raw = _phenom_people_jsonld(doc).get("description")
    if not raw:
        return None
    result = md(_html.unescape(raw), heading_style="ATX", bullets="-", strip=["a", "img"]).strip()
    return result or None


def _phenom_people_title(doc: BeautifulSoup, url: str) -> str | None:
    title = _phenom_people_jsonld(doc).get("title")
    return title.strip() or None if isinstance(title, str) else None


def _phenom_people_role_type(doc: BeautifulSoup, url: str) -> str | None:
    types = _phenom_people_jsonld(doc).get("employmentType")
    if not types:
        return None
    joined = " ".join(types if isinstance(types, list) else [types]).upper()
    if "FULL_TIME" in joined:
        return "full-time"
    if "PART_TIME" in joined:
        return "part-time"
    if "CONTRACT" in joined:
        return "contract"
    if "INTERN" in joined:
        return "internship"
    return None


ADAPTER: dict[str, Any] = {
    "title": _phenom_people_title,
    "location": _phenom_people_location,
    "description": _phenom_people_description,
    "role_type": _phenom_people_role_type,
}
