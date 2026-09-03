# ---------------------------------------------------------------------------
# Wayve (wayve.firststage.co) — First Stage ATS job board. The visible <h1>
# concatenates an "Apply for" button label, the job title, and a run of
# location/employment-type/department pill tags with no separators (the
# generic adapter's `get_text(separator=" ")` over that h1 produces garbage
# like "Apply for <title> Sunnyvale, California USA ... full time on-site
# Product & Delivery"). company_name and role_type already resolve correctly
# via the generic adapter (og:site_name meta / body text), so only title,
# location, and description are overridden here, all sourced from the
# <script type="application/ld+json"> JobPosting block that First Stage
# embeds on every listing page.
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "wayve.firststage.co"


def _wayve_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    for s in doc.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string or "")
            if d.get("@type") == "JobPosting":
                return d  # type: ignore[no-any-return]
        except Exception:
            pass
    return {}


def _wayve_title(doc: BeautifulSoup, url: str) -> str | None:
    return _wayve_jsonld(doc).get("title") or None


def _wayve_location(doc: BeautifulSoup, url: str) -> str | None:
    job_location = _wayve_jsonld(doc).get("jobLocation") or {}
    address = job_location.get("address")
    if isinstance(address, str) and address.strip():
        return address.strip()
    return None


def _wayve_description(doc: BeautifulSoup, url: str) -> str | None:
    raw = _wayve_jsonld(doc).get("description") or ""
    if not raw:
        return None
    return _to_markdown(BeautifulSoup(raw, "lxml"))


ADAPTER: dict[str, Any] = {
    "title": _wayve_title,
    "location": _wayve_location,
    "description": _wayve_description,
}
