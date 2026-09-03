# ---------------------------------------------------------------------------
# CoreWeave (coreweave.com) — the real job description/apply flow is a
# cross-origin Greenhouse iframe scout_fetch can't see, so scout_fetch
# fetches Greenhouse's public Jobs API instead and hands this adapter
# synthetic HTML with the fields under fixed classes (see
# jobforce.cli.scout_fetch._fetch_coreweave_greenhouse_html).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "coreweave.com"


def _coreweave_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".coreweave-gh-title"))


def _coreweave_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".coreweave-gh-location"))


def _coreweave_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".coreweave-gh-description"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "CoreWeave",
    "title": _coreweave_title,
    "location": _coreweave_location,
    "description": _coreweave_description,
}
