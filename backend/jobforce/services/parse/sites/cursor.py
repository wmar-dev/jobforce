# ---------------------------------------------------------------------------
# Cursor site adapter — cursor.com/careers/<slug>
# Page structure: main > article > div > header > h1 + p (dept·type·location)
#                                       div > div.prose (description)
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "cursor.com"


def _cursor_location(doc: BeautifulSoup, url: str) -> str | None:
    # "Engineering · Full-time · San Francisco; New York" — take last segment
    p = doc.select_one("main article header p")
    if p and (t := _text(p)):
        parts = [x.strip() for x in t.split("·")]
        if len(parts) >= 3:
            return parts[-1] or None
    return None


def _cursor_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".prose")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Cursor",
    "location": _cursor_location,
    "description": _cursor_description,
}
