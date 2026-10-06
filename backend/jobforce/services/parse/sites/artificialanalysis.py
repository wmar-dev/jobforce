# ---------------------------------------------------------------------------
# Artificial Analysis (artificialanalysis.ai) — Next.js careers page. A
# <header> holds a row of metadata spans (team, employment type, location —
# the location span is last) above the h1 title. The role body is the
# ".space-y-10" sibling that follows the header.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "artificialanalysis.ai"


def _artificialanalysis_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    header = h1.find_parent("header") if h1 else None
    if not header:
        return None
    spans = [s for s in header.select("span") if _text(s)]
    return _text(spans[-1]) if spans else None


def _artificialanalysis_description(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    header = h1.find_parent("header") if h1 else None
    if not header:
        return None
    return _to_markdown(header.find_next_sibling("div", class_="space-y-10"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Artificial Analysis",
    "location": _artificialanalysis_location,
    "description": _artificialanalysis_description,
}
