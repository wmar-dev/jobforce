# ---------------------------------------------------------------------------
# Coinbase (coinbase.com/careers/positions/<id>) — title extracts fine via
# the generic adapter's <h1>. Location is the first of two <span> tags in
# the div right after the <h1>. Coinbase renders Greenhouse's job content
# HTML directly, including its ".content-intro" wrapper div, so the
# description container is that div's parent — same pattern as Brex.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "coinbase.com"


def _coinbase_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    sib = h1.find_next_sibling("div")
    if sib is None:
        return None
    return _text(sib.select_one("span"))


def _coinbase_description(doc: BeautifulSoup, url: str) -> str | None:
    intro = doc.select_one(".content-intro")
    if intro is None:
        return None
    container = intro.find_parent("div")
    return _to_markdown(container)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Coinbase",
    "location": _coinbase_location,
    "description": _coinbase_description,
}
