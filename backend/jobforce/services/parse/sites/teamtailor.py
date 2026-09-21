# ---------------------------------------------------------------------------
# Teamtailor (*.teamtailor.com) — every job page embeds a full schema.org
# JobPosting JSON-LD block (<script type="application/ld+json">) with
# location and description, so parse both fields from there rather than the
# rendered DOM. The JSON-LD `description` value is itself HTML-escaped
# (literal `&lt;p&gt;` text), so run it through `normalize_description`.
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .._common import normalize_description

HOSTNAME = "teamtailor.com"


def _teamtailor_jsonld(doc: BeautifulSoup) -> dict[str, Any] | None:
    script = doc.find("script", attrs={"type": "application/ld+json"})
    if script is None or not script.string:
        return None
    try:
        data = json.loads(script.string)
    except ValueError:
        return None
    return data if isinstance(data, dict) else None


def _teamtailor_location(doc: BeautifulSoup, url: str) -> str | None:
    data = _teamtailor_jsonld(doc)
    if data is None:
        return None
    locations = data.get("jobLocation") or []
    if not locations:
        return None
    address = locations[0].get("address") or {}
    parts = [address.get("addressLocality"), address.get("addressCountry")]
    joined = ", ".join(p for p in parts if p)
    return joined or None


def _teamtailor_description(doc: BeautifulSoup, url: str) -> str | None:
    data = _teamtailor_jsonld(doc)
    if data is None:
        return None
    return normalize_description(data.get("description"))


ADAPTER: dict[str, Any] = {
    "location": _teamtailor_location,
    "description": _teamtailor_description,
}
