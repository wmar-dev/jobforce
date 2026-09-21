# ---------------------------------------------------------------------------
# Jobvite (jobs.jobvite.com) — every job page embeds a full schema.org
# JobPosting JSON-LD block. The <title> tag reads "<Company> Careers -
# <Job Title>", which the generic adapter's title-tag fallback strips down
# to just "<Company> Careers", so title needs an override too even though
# company_name would already work off it.
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .._common import normalize_description

HOSTNAME = "jobs.jobvite.com"


def _jobvite_jsonld(doc: BeautifulSoup) -> dict[str, Any] | None:
    script = doc.find("script", attrs={"type": "application/ld+json"})
    if script is None or not script.string:
        return None
    try:
        data = json.loads(script.string)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _jobvite_title(doc: BeautifulSoup, url: str) -> str | None:
    data = _jobvite_jsonld(doc)
    if data is None:
        return None
    title = data.get("title")
    return title.strip() if isinstance(title, str) and title.strip() else None


def _jobvite_company(doc: BeautifulSoup, url: str) -> str | None:
    data = _jobvite_jsonld(doc)
    if data is None:
        return None
    org = data.get("hiringOrganization")
    if isinstance(org, dict):
        name = org.get("name")
        return name.strip() if isinstance(name, str) and name.strip() else None
    if isinstance(org, str) and org.strip():
        return org.strip()
    return None


def _jobvite_location(doc: BeautifulSoup, url: str) -> str | None:
    data = _jobvite_jsonld(doc)
    if data is None:
        return None
    locations = data.get("jobLocation") or []
    if not locations:
        return None
    address = locations[0].get("address") or {}
    parts = [
        address.get("addressLocality"),
        address.get("addressRegion"),
        address.get("addressCountry"),
    ]
    joined = ", ".join(p for p in parts if p)
    return joined or None


def _jobvite_description(doc: BeautifulSoup, url: str) -> str | None:
    data = _jobvite_jsonld(doc)
    if data is None:
        return None
    return normalize_description(data.get("description"))


ADAPTER: dict[str, Any] = {
    "title": _jobvite_title,
    "company_name": _jobvite_company,
    "location": _jobvite_location,
    "description": _jobvite_description,
}
