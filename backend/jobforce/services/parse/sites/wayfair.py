# ---------------------------------------------------------------------------
# Wayfair careers (www.wayfair.com/careers) — job metadata is a
# `<dl class="CareersJobDetailsDisplayDescription-list">` of term/value pairs
# ("Location:", "Category:", ...) with no `.location` class, and the body is
# `.CareersJobDetailsDisplayDescription-jobDescription` (capital-D
# "Description", so the generic `[class*="description"]` selector misses it).
# title/company_name resolve via the generic h1 / og:site_name fallbacks.
# The live site 429s headless browsers intermittently; scout_fetch's stored
# snapshot is the reliable source for fixtures.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "wayfair.com"


def _wayfair_location(doc: BeautifulSoup, url: str) -> str | None:
    for dt in doc.select("dt.CareersJobDetailsDisplayDescription-listTerm"):
        if (_text(dt) or "").rstrip(":").strip().lower() == "location":
            loc = _text(dt.find_next_sibling("dd"))
            if loc:
                # dd text is "&nbsp;Mountain View,&nbsp;California"
                return " ".join(loc.replace("\xa0", " ").split()).replace(" ,", ",") or None
    return None


def _wayfair_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".CareersJobDetailsDisplayDescription-jobDescription"))


ADAPTER: dict[str, Any] = {
    "location": _wayfair_location,
    "description": _wayfair_description,
}
