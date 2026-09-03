# ---------------------------------------------------------------------------
# Turing site adapter — careers.turing.com/job/<id>
# Page structure: div[class*="job-details-title"] = job title
#                 div[class*="job-details-location"] = "Location: <cities>"
#                 div[class*="job-details-description"] = full job description
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careers.turing.com"


def _turing_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="job-details-title"]')
    return _text(el)


def _turing_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="job-details-location"]')
    if not el:
        return None
    t = _text(el) or ""
    # Strip "Location: " prefix
    if t.lower().startswith("location:"):
        t = t[len("location:") :].strip()
    return t or None


def _turing_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="job-details-description"]')
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Turing",
    "title": _turing_title,
    "location": _turing_location,
    "description": _turing_description,
}
