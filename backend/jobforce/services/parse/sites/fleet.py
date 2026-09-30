# ---------------------------------------------------------------------------
# Fleet (fleetai.com/careers/<slug>) — Next.js page with Tailwind utility classes
# Page structure: article > h1 (title) + div.flex-wrap > span chips (location, work mode, type)
#                 div.tiptap (description)
# Note: no company element; the name is the "| Fleet" suffix of <title>.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "fleetai.com"


def _fleet_company(doc: BeautifulSoup, url: str) -> str | None:
    return "Fleet"


def _fleet_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.find("h1")
    if h1:
        chips = h1.find_next_sibling("div")
        if chips:
            return _text(chips.find("span"))
    return None


def _fleet_description(doc: BeautifulSoup, url: str) -> str | None:
    for div in doc.find_all("div"):
        if "tiptap" in (div.get("class") or []):
            return _to_markdown(div)
    return None


ADAPTER: dict[str, Any] = {
    "company_name": _fleet_company,
    "location": _fleet_location,
    "description": _fleet_description,
}
