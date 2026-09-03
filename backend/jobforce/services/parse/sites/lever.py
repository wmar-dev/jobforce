# ---------------------------------------------------------------------------
# Lever site adapter — jobs.lever.co/<company>/<job-id>
# Page structure: div.posting-headline > h2 (title) + div.posting-categories
#                   > div[0]=location, div[1]=team, div[2]=commitment, div[3]=worktype
#                 div.section-wrapper > (job description sections)
# Note: Lever escapes class names in HTML so CSS selectors fail; navigate by position.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "jobs.lever.co"


def _lever_company(doc: BeautifulSoup, url: str) -> str | None:
    # Prefer "Company - Job Title" in <title> tag for canonical casing
    title_tag = doc.find("title")
    if title_tag:
        raw = (title_tag.get_text() or "").strip()
        parts = raw.split(" - ", 1)
        if len(parts) == 2:
            return parts[0].strip() or None
    # Fallback: extract from URL path jobs.lever.co/<company>/<id>
    parts = urlparse(url).path.strip("/").split("/")
    if parts and parts[0]:
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _lever_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.find("h2"))


def _lever_location(doc: BeautifulSoup, url: str) -> str | None:
    h2 = doc.find("h2")
    if h2:
        cats = h2.find_next_sibling("div")
        if cats:
            divs = cats.find_all("div", recursive=False)
            if divs:
                return _text(divs[0])
    return None


def _lever_role_type(doc: BeautifulSoup, url: str) -> str | None:
    h2 = doc.find("h2")
    if h2:
        cats = h2.find_next_sibling("div")
        if cats:
            divs = cats.find_all("div", recursive=False)
            if len(divs) >= 3:
                raw = _text(divs[2]) or ""
                raw = raw.rstrip(" /").lower()
                if "full" in raw:
                    return "full-time"
                if "part" in raw:
                    return "part-time"
                if "contract" in raw:
                    return "contract"
                if "intern" in raw:
                    return "internship"
    return None


def _lever_description(doc: BeautifulSoup, url: str) -> str | None:
    # Lever wraps job content in div.section-wrapper.page-full-width (not accent-section/main-header).
    # class values may be HTML-escaped (e.g. '"section-wrapper"') in some fixtures; use substring match.
    for div in doc.find_all("div"):
        classes_str = " ".join(str(c) for c in div.get("class") or [])
        if "section-wrapper" not in classes_str:
            continue
        if "accent-section" in classes_str or "main-header" in classes_str:
            continue
        text = div.get_text(strip=True)
        if len(text) > 50:
            return _to_markdown(div)
    return None


ADAPTER: dict[str, Any] = {
    "company_name": _lever_company,
    "title": _lever_title,
    "location": _lever_location,
    "role_type": _lever_role_type,
    "description": _lever_description,
}
