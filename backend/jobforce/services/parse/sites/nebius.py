# ---------------------------------------------------------------------------
# Nebius (careers.nebius.com) — the real job description/apply flow is a
# cross-origin Greenhouse iframe scout_fetch can't see, so scout_fetch
# fetches Greenhouse's public Jobs API instead and hands this adapter
# synthetic HTML with the fields under fixed classes (see
# jobforce.cli.scout_fetch._fetch_nebius_greenhouse_html).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careers.nebius.com"


def _nebius_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".nebius-gh-title"))


def _nebius_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".nebius-gh-location"))


def _nebius_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".nebius-gh-description"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Nebius",
    "title": _nebius_title,
    "location": _nebius_location,
    "description": _nebius_description,
}
