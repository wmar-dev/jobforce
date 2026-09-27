# ---------------------------------------------------------------------------
# Moss (moss.dev) — the page carries a clean schema.org JobPosting JSON-LD
# block, but its own `description` field is a one-line summary rather than
# the full body, so location comes from JSON-LD while description still
# comes from the DOM's #job-panel-overview tabpanel.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown, find_jobposting_jsonld

HOSTNAME = "moss.dev"


def _moss_location(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    if data is None:
        return None
    address = (data.get("jobLocation") or {}).get("address") or {}
    locality = address.get("addressLocality")
    region = address.get("addressRegion")
    parts = [p for p in (locality, region) if p]
    location = ", ".join(parts) if parts else None
    if data.get("jobLocationType") == "TELECOMMUTE":
        location = f"{location} / Remote" if location else "Remote"
    return location


def _moss_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("#job-panel-overview"))


ADAPTER: dict[str, Any] = {
    "location": _moss_location,
    "description": _moss_description,
}
