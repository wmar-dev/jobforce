# ---------------------------------------------------------------------------
# Etsy careers (careers.etsy.com) — no og:site_name or company element, so
# the generic company fallback returns None and scout_fetch rejects the page;
# the generic `.location` selector matches the referral form's Location
# dropdown (a list of countries) rather than the job's location. The ld+json
# JobPosting block has the hiring organization, a jobLocation list, a
# `jobLocationType: TELECOMMUTE` flag for "Open to Remote" roles, and the full
# description — all four fields are pulled from there.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown, find_jobposting_jsonld

HOSTNAME = "careers.etsy.com"


def _etsy_company(doc: BeautifulSoup, url: str) -> str | None:
    org = (find_jobposting_jsonld(doc) or {}).get("hiringOrganization") or {}
    name = org.get("name") if isinstance(org, dict) else None
    return name.strip() if isinstance(name, str) and name.strip() else "Etsy"


def _etsy_location(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc) or {}
    places = data.get("jobLocation") or []
    if isinstance(places, dict):
        places = [places]
    locs: list[str] = []
    for place in places:
        addr = place.get("address") or {}
        loc = ", ".join(p for p in (addr.get("addressLocality"), addr.get("addressRegion")) if p)
        if loc and loc not in locs:
            locs.append(loc)
    if data.get("jobLocationType") == "TELECOMMUTE":
        locs.append("Remote")
    return "; ".join(locs) or None


def _etsy_description(doc: BeautifulSoup, url: str) -> str | None:
    raw = (find_jobposting_jsonld(doc) or {}).get("description") or ""
    if not raw:
        return None
    return _to_markdown(BeautifulSoup(raw, "lxml"))


ADAPTER: dict[str, Any] = {
    "company_name": _etsy_company,
    "location": _etsy_location,
    "description": _etsy_description,
}
