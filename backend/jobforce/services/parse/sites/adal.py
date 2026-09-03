# ---------------------------------------------------------------------------
# SylphAI (adalagent.ai) — custom React SPA; company name and location both
# come from the subtitle paragraph ("SylphAI. San Francisco, United States.").
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "adalagent.ai"


def _adal_location(doc: BeautifulSoup, url: str) -> str | None:
    # Subtitle: "SylphAI. San Francisco, United States." — drop the company prefix
    el = doc.select_one("p.text-adal-text-secondary, p.italic")
    if not el:
        return None
    text = _text(el) or ""
    # Strip leading "SylphAI. " (or any "Word. " prefix before the location)
    parts = text.split(". ", 1)
    location = parts[1] if len(parts) == 2 else text
    return location.rstrip(".").strip() or None


def _adal_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "SylphAI",
    "location": _adal_location,
    "description": _adal_description,
}
