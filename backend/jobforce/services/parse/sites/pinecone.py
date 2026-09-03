# ---------------------------------------------------------------------------
# Pinecone site adapter — pinecone.io/careers/<uuid>/
# Page structure: main > div > div > div.container.py-50 >
#                   a(All Jobs), h1, p("at Company, Location"), div(desc), div(apply)
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "pinecone.io"


def _pinecone_company(doc: BeautifulSoup, url: str) -> str | None:
    # "at Pinecone, New York City" — extract company name
    p = doc.select_one("main p")
    if p and (t := _text(p)):
        m = re.match(r"at\s+(.+?),\s+.+", t.strip())
        if m:
            return m.group(1).strip() or None
    return "Pinecone"


def _pinecone_location(doc: BeautifulSoup, url: str) -> str | None:
    # "at Pinecone, New York City" — extract location after company
    p = doc.select_one("main p")
    if p and (t := _text(p)):
        m = re.match(r"at\s+.+?,\s+(.+)", t.strip())
        if m:
            return m.group(1).strip() or None
    return None


def _pinecone_description(doc: BeautifulSoup, url: str) -> str | None:
    container = doc.select_one("main div.container, main div[class*='py-50']")
    if container:
        for div in container.find_all("div", recursive=False):
            t = _text(div)
            if t and len(t) > 100:
                return _to_markdown(div)
    return None


ADAPTER: dict[str, Any] = {
    "company_name": _pinecone_company,
    "location": _pinecone_location,
    "description": _pinecone_description,
}
