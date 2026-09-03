# ---------------------------------------------------------------------------
# Larridin (larridin.com) — HubSpot CMS page. Job header is a ".headings" div
# (h1 title) followed by a sibling ".col-content" div holding the location
# paragraph. Job body content lives in one or more ".sr-richtext" divs.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "larridin.com"


def _larridin_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if not h1:
        return None
    headings = h1.find_parent("div", class_="headings")
    if not headings:
        return None
    col_content = headings.find_next_sibling("div", class_="col-content")
    return _text(col_content)


def _larridin_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [md for el in doc.select(".sr-richtext") if (md := _to_markdown(el))]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Larridin",
    "location": _larridin_location,
    "description": _larridin_description,
}
