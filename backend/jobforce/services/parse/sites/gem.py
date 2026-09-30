# ---------------------------------------------------------------------------
# Gem (jobs.gem.com/<company>/<job-id>) — multi-tenant ATS
# Page structure: div[class^=jobPostingHeader-] (title, the one with no children divs)
#                 div[class^=attributesContainer-] > first child > span (location)
#                 div[class^=typography-] (description; sibling form container excluded)
# Note: class names carry numeric suffixes (e.g. "jobPostingHeader-29") that change
#       between builds, so match on the prefix. The company name only appears in the URL slug.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "jobs.gem.com"


def _by_class_prefix(doc: BeautifulSoup, prefix: str) -> list[Tag]:
    return [
        el
        for el in doc.find_all("div")
        if any(str(c).startswith(prefix) for c in el.get("class") or [])
    ]


def _gem_company(doc: BeautifulSoup, url: str) -> str | None:
    parts = urlparse(url).path.strip("/").split("/")
    if parts and parts[0]:
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _gem_title(doc: BeautifulSoup, url: str) -> str | None:
    # Two elements share the jobPostingHeader- prefix; the title is the leaf one.
    for el in _by_class_prefix(doc, "jobPostingHeader-"):
        if not el.find("div"):
            return _text(el)
    return None


def _gem_location(doc: BeautifulSoup, url: str) -> str | None:
    for attrs in _by_class_prefix(doc, "attributesContainer-"):
        span = attrs.find("span")
        if span:
            return _text(span)
    return None


def _gem_description(doc: BeautifulSoup, url: str) -> str | None:
    for el in _by_class_prefix(doc, "typography-"):
        return _to_markdown(el)
    return None


ADAPTER: dict[str, Any] = {
    "company_name": _gem_company,
    "title": _gem_title,
    "location": _gem_location,
    "description": _gem_description,
}
