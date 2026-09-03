# ---------------------------------------------------------------------------
# Airbnb careers site — careers.airbnb.com/positions/<id>
# Page structure: h1 (title), next sibling text node = location,
#                 main section paragraphs = description
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careers.airbnb.com"


def _airbnb_location(doc: BeautifulSoup, url: str) -> str | None:
    # Location is in the first div sibling after h1
    h1 = doc.select_one("h1")
    if h1:
        el = h1.find_next_sibling("div")
        if el and (t := _text(el)):
            return t
    return None


def _airbnb_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("#job-detail-panel, .job-detail")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Airbnb",
    "location": _airbnb_location,
    "description": _airbnb_description,
}
