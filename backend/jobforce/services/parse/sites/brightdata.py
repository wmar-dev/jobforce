# ---------------------------------------------------------------------------
# Bright Data (brightdata.com) — WordPress careers pages. The <title> is the
# generic "Careers | Open Job Positions" string, but the h1 inside .single_pos
# is correct; location is the ".loc" block, the body is ".requirements".
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "brightdata.com"


def _brightdata_location(doc: BeautifulSoup, url: str) -> str | None:
    loc = doc.select_one(".single_pos .loc")
    if loc is None:
        return None
    text = " ".join(loc.get_text(" ", strip=True).split())
    # Remote postings render with empty country/city: ", (Remote)" -> "(Remote)"
    return text.lstrip(", ") or None


def _brightdata_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".single_pos .requirements"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Bright Data",
    "location": _brightdata_location,
    "description": _brightdata_description,
}
