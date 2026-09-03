# ---------------------------------------------------------------------------
# Ashby site adapter — jobs.ashbyhq.com
# URL: jobs.ashbyhq.com/<company>/<job-id>
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import unquote, urlparse

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "jobs.ashbyhq.com"

_ASHBY_SLUG_COMPANY_OVERRIDES = {
    # Some companies' Ashby board slugs don't match their real name
    # (e.g. jobs.ashbyhq.com/frontcareers/... is Front, not "Frontcareers").
    "frontcareers": "Front",
    # Grammarly's board is under its parent brand's legal entity name.
    "superhuman platform inc": "Grammarly",
}


def _ashby_company(doc: BeautifulSoup, url: str) -> str | None:
    # Extract company from URL path: jobs.ashbyhq.com/figma/... → Figma
    parts = urlparse(url).path.strip("/").split("/")
    if parts and parts[0]:
        slug = unquote(parts[0])
        if override := _ASHBY_SLUG_COMPANY_OVERRIDES.get(slug.lower()):
            return override
        return " ".join(w.capitalize() for w in slug.replace("-", " ").split())
    return None


def _ashby_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ashby-job-posting-heading, .ashby-job-posting-brief-description h1")
    return _text(el)


def _ashby_location(doc: BeautifulSoup, url: str) -> str | None:
    # Current markup: left pane has <h2>Location</h2><p>San Francisco</p> sections
    for section in doc.select(
        ".ashby-job-posting-left-pane ._section_101oc_37, .ashby-job-posting-left-pane [class*='_section']"
    ):
        h2 = section.find("h2")
        if h2 and "location" in (h2.get_text() or "").lower():
            p = section.find("p")
            if p and (t := _text(p)):
                return t
    # Fallback: legacy brief-description items
    items = doc.select(".ashby-job-posting-brief-description-item")
    if items:
        return _text(items[0])
    return None


def _ashby_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ashby-job-posting-description")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": _ashby_company,
    "title": _ashby_title,
    "location": _ashby_location,
    "description": _ashby_description,
}
