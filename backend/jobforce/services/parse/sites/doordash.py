# ---------------------------------------------------------------------------
# DoorDash (careersatdoordash.com/jobs/<slug>/<id>) — title and company_name
# already extract fine via the generic adapter; location and description
# need dedicated selectors.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careersatdoordash.com"


def _doordash_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("#jd-location"))


def _doordash_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".content"))


ADAPTER: dict[str, Any] = {
    "location": _doordash_location,
    "description": _doordash_description,
}
