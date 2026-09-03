# ---------------------------------------------------------------------------
# Akuna Capital careers (akunacapital.com) — a WordPress theme rendering
# Greenhouse-sourced job data server-side. title/company_name/description
# already resolve fine via the generic adapter (`h1`, `og:site_name`, and a
# ".job-description"-suffixed class all match). location and role_type are
# both broken: location has no ".location"/"[data-location]" element (the
# rendered text sits in an unclassed `<span>` inside a `<p class="sub">`
# under the hero `<h1>`), and the generic role_type body-text scan matches
# the standalone word "Intern" in unrelated boilerplate every listing
# repeats ("...take a look at our Entry Level and Intern positions"),
# misreporting "internship" for full-time roles. Both fields are pulled
# instead from the `<script type="application/ld+json">` JobPosting block
# the page also embeds (same pattern as the Box/Workable adapters), which
# is authoritative and unaffected by boilerplate text elsewhere on the page.
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

HOSTNAME = "akunacapital.com"


def _akuna_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    for s in doc.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string or "")
        except Exception:
            continue
        if d.get("@type") == "JobPosting":
            return d  # type: ignore[no-any-return]
    return {}


def _akuna_location(doc: BeautifulSoup, url: str) -> str | None:
    d = _akuna_jsonld(doc)
    addr = (d.get("jobLocation") or {}).get("address") or {}
    city = addr.get("addressLocality", "")
    region = addr.get("addressRegion", "")
    if d.get("jobLocationType") == "TELECOMMUTE":
        return f"{city} (Remote)" if city else "Remote"
    if city and region:
        return f"{city}, {region}"
    return city or region or None


def _akuna_role_type(doc: BeautifulSoup, url: str) -> str | None:
    d = _akuna_jsonld(doc)
    emp = (d.get("employmentType") or "").upper()
    return {
        "FULL_TIME": "full-time",
        "PART_TIME": "part-time",
        "CONTRACTOR": "contract",
        "INTERN": "internship",
    }.get(emp)


ADAPTER: dict[str, Any] = {
    "location": _akuna_location,
    "role_type": _akuna_role_type,
}
