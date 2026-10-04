# ---------------------------------------------------------------------------
# Deel ATS (jobs.deel.com) — multi-tenant Next.js/MUI career pages
# (/<company-slug>/job-details/<uuid>/overview). There is no <h1> element, so
# title, company, and location come from the schema.org JobPosting JSON-LD
# block; the description is the ".RichTextDisplay" container.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown, find_jobposting_jsonld

HOSTNAME = "jobs.deel.com"


def _deel_title(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    title = data.get("title") if data else None
    return title.strip() if isinstance(title, str) and title.strip() else None


def _deel_company(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    org = data.get("hiringOrganization") if data else None
    name = org.get("name") if isinstance(org, dict) else None
    return name.strip() if isinstance(name, str) and name.strip() else None


def _deel_location(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    places = data.get("jobLocation") if data else None
    if isinstance(places, dict):
        places = [places]
    if not isinstance(places, list):
        return None
    parts: list[str] = []
    for place in places:
        address = place.get("address") if isinstance(place, dict) else None
        locality = address.get("addressLocality") if isinstance(address, dict) else None
        if isinstance(locality, str) and (loc := locality.strip()) and loc not in parts:
            parts.append(loc)
    return "; ".join(parts) or None


def _deel_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one('[class*="richTextDisplay"]'))


ADAPTER: dict[str, Any] = {
    "title": _deel_title,
    "company_name": _deel_company,
    "location": _deel_location,
    "description": _deel_description,
}
