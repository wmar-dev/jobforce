# ---------------------------------------------------------------------------
# Keenable (app.keenable.ai) — the page has a hidden sitewide tagline <h1>
# ("Keenable — Search for AI agents") before the real job title <h1>, so
# title is pinned to the CSS-modules title class; location and employment
# type are combined in one "Full-time · Remote — Worldwide" element.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "app.keenable.ai"


def _keenable_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('h1[class*="_Title_"]'))


def _keenable_location(doc: BeautifulSoup, url: str) -> str | None:
    role_meta = _text(doc.select_one('p[class*="_RoleMeta_"]'))
    if role_meta is None:
        return None
    _, _, location = role_meta.partition("·")
    return location.strip() or None


def _keenable_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one('div[class*="_Description_"]'))


ADAPTER: dict[str, Any] = {
    "title": _keenable_title,
    "location": _keenable_location,
    "description": _keenable_description,
}
