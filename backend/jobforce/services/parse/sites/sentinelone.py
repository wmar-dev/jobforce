# ---------------------------------------------------------------------------
# SentinelOne (sentinelone.com) — the real job description/apply flow is a
# cross-origin Greenhouse iframe scout_fetch can't see, so scout_fetch
# fetches Greenhouse's public Jobs API instead and hands this adapter
# synthetic HTML with the fields under fixed classes (see
# jobforce.cli.scout_fetch._fetch_sentinelone_greenhouse_html).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "sentinelone.com"


def _sentinelone_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".sentinelone-gh-title"))


def _sentinelone_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".sentinelone-gh-location"))


def _sentinelone_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".sentinelone-gh-description"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "SentinelOne",
    "title": _sentinelone_title,
    "location": _sentinelone_location,
    "description": _sentinelone_description,
}
