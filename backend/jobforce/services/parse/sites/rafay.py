# ---------------------------------------------------------------------------
# Rafay (rafay.co) — Webflow careers pages. The h1 packs "<title>", " - " and
# "<location>" into three spans; location also appears in .career_meta_location;
# the job body is the .rich-text block.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "rafay.co"


def _rafay_title(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    first = h1.find("span")
    return _text(first) if first is not None else _text(h1)


def _rafay_location(doc: BeautifulSoup, url: str) -> str | None:
    box = doc.select_one(".career_meta_location")
    if box is None:
        return None
    divs = box.find_all("div", recursive=False)
    return _text(divs[-1]) if divs else None


def _rafay_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".rich-text"))


ADAPTER: dict[str, Any] = {
    "title": _rafay_title,
    "company_name": lambda doc, url: "Rafay",
    "location": _rafay_location,
    "description": _rafay_description,
}
