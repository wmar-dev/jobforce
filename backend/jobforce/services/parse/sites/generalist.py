# ---------------------------------------------------------------------------
# Generalist AI (generalistai.com) — job body has multiple <h1> section
# headings ("About Generalist", "About the Role") alongside the real job
# title, so title is pinned to h1.job-title instead of DOM-order luck;
# location lives in a metadata table row rather than a location element.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "generalistai.com"


def _generalist_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h1.job-title"))


def _generalist_location(doc: BeautifulSoup, url: str) -> str | None:
    label = doc.find("th", string=lambda t: bool(t and t.strip() == "Location"))
    if label is None:
        return None
    return _text(label.find_next_sibling("td"))


def _generalist_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("section.job-content"))


ADAPTER: dict[str, Any] = {
    "title": _generalist_title,
    "location": _generalist_location,
    "description": _generalist_description,
}
