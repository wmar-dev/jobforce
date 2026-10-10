# ---------------------------------------------------------------------------
# Lane (getonlane.com) — Next.js careers pages. Each role page carries a
# schema.org JobPosting JSON-LD block (location + HTML description) but has no
# og:site_name or description class hooks for the generic adapter.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown, find_jobposting_jsonld

HOSTNAME = "getonlane.com"


def _lane_location(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    loc = data.get("jobLocation") if data else None
    address = loc.get("address") if isinstance(loc, dict) else None
    if not isinstance(address, dict):
        return None
    parts = [address.get("addressLocality"), address.get("addressRegion")]
    return ", ".join(p for p in parts if isinstance(p, str) and p) or None


def _lane_description(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    html = data.get("description") if data else None
    if not isinstance(html, str) or not html.strip():
        return None
    return _to_markdown(BeautifulSoup(html, "html.parser"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Lane",
    "location": _lane_location,
    "description": _lane_description,
}
