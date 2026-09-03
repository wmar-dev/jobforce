# ---------------------------------------------------------------------------
# OpenAI site adapter — equivalent to openaiAdapter in content.js
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown, slug_to_location

HOSTNAME = "openai.com"

_LOCATION_KEYWORDS = re.compile(
    r"\b(san francisco|new york|seattle|london|boston|chicago|austin|remote)\b",
    re.IGNORECASE,
)


def _openai_location(doc: BeautifulSoup, url: str) -> str | None:
    # First h2 in main is the job title; its next sibling p is the dept/location line
    # e.g. "Robotics - San Francisco" or "Applied AI Engineering - San Francisco and Seattle"
    # Guard: some pages put a team description <p> before the location — skip those.
    # Current hero markup wraps the subhead <p> in a <div> after the h2 rather than
    # making it a direct sibling, so check the explicit data attribute first —
    # it survives that nesting change and multi-location "X, Y, and Z" text alike.
    subhead = doc.select_one('[data-article-hero-copy-region="subhead"]')
    if subhead and (t := _text(subhead)):
        return t
    title_h2 = doc.select_one("main h2")
    if title_h2:
        el = title_h2.find_next_sibling("p")
        if el and (t := _text(el)):
            if _LOCATION_KEYWORDS.search(t):
                return t
    return slug_to_location(urlparse(url).path)


def _openai_compensation(doc: BeautifulSoup, url: str) -> str | None:
    for el in doc.select("main p"):
        t = (el.get_text() or "").strip()
        if t.startswith("$"):
            return t
    return None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "OpenAI",
    "title": lambda doc, url: _text(doc.select_one("main h2")),
    "location": _openai_location,
    "description": lambda doc, url: _to_markdown(
        doc.select_one("main article, main section, main div")
    ),
    "compensation": _openai_compensation,
}
