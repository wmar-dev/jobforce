# ---------------------------------------------------------------------------
# Kula (careers.kula.ai) — every job page embeds a full schema.org JobPosting
# JSON-LD block; title and company_name already resolve via the generic
# adapter (h1, and the <title> tag's "<Job Title> - <Company>" order matches
# its stripping assumption), so this adapter only covers location and
# description.
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .._common import normalize_description

HOSTNAME = "careers.kula.ai"


def _kula_jsonld(doc: BeautifulSoup) -> dict[str, Any] | None:
    script = doc.find("script", attrs={"type": "application/ld+json"})
    if script is None or not script.string:
        return None
    try:
        data = json.loads(script.string)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _kula_location(doc: BeautifulSoup, url: str) -> str | None:
    data = _kula_jsonld(doc)
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


def _kula_description(doc: BeautifulSoup, url: str) -> str | None:
    data = _kula_jsonld(doc)
    if data is None:
        return None
    return normalize_description(data.get("description"))


ADAPTER: dict[str, Any] = {
    "location": _kula_location,
    "description": _kula_description,
}
