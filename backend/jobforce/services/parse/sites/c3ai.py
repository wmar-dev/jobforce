# ---------------------------------------------------------------------------
# C3.ai (c3.ai) — Next.js job page. Title is a bare <h1>, location/department
# share one <p> right after it ("City, ST · Department"), and the full JD
# lives in the wrapper <div> that follows the "Apply Now" button.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "c3.ai"


def _c3ai_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    p = h1.find_next_sibling("p")
    if p is None:
        return None
    text = _text(p) or ""
    location = text.split("·", 1)[0].strip()
    return location or None


def _c3ai_description(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    button = h1.find_next_sibling("button")
    if button is None:
        return None
    wrapper = button.find_next_sibling("div")
    return _to_markdown(wrapper)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "C3 AI",
    "location": _c3ai_location,
    "description": _c3ai_description,
}
