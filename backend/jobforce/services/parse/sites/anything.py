# ---------------------------------------------------------------------------
# Anything (create.xyz, rebranded from Create) — job body includes a content
# <h1> ("What this role is") below the real title, which sits in an <h2>, so
# the generic h1-first title lookup grabs the wrong heading.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "create.xyz"


def _anything_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h2"))


def _anything_location(doc: BeautifulSoup, url: str) -> str | None:
    h2 = doc.select_one("h2")
    if h2 is None:
        return None
    return _text(h2.find_next_sibling())


def _anything_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".prose"))


ADAPTER: dict[str, Any] = {
    "title": _anything_title,
    "company_name": lambda doc, url: "Anything",
    "location": _anything_location,
    "description": _anything_description,
}
