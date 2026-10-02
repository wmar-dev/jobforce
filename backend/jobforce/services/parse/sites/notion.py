# ---------------------------------------------------------------------------
# Notion site adapter — <company>.notion.site/<page-id>
# Notion public pages render React-driven HTML. Key signals:
#   - Company name: URL subdomain, with casing from topbar breadcrumb
#   - Title: <title> tag / og:title (reliable)
#   - Properties (Location, Employment Type, Department): extracted from
#     the flat text stream because Notion generates anonymous class names.
#     Properties appear as consecutive lines: "Location\nRemote\nSan Francisco\n..."
#     terminated by the next property name or by "What we do" / page content.
#   - Description: .notion-page-content text (starts after property block)
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _generic_role_type, _text, _to_markdown

HOSTNAME = "notion.site"

_NOTION_PROPERTY_NAMES = {
    "Department",
    "Employment Type",
    "Location",
    "Created",
    "Last edited time",
}

_NOTION_PROPERTY_HEADINGS = {
    "What we do",
    "What we want",
    "What you want",
    "What you've done",
    "About the role",
    "About us",
    "About you",
    "Requirements",
    "Responsibilities",
    "Qualifications",
    "Benefits",
    "Compensation",
}


def _notion_text_lines(doc: BeautifulSoup) -> list[str]:
    return [line.strip() for line in doc.get_text(separator="\n").split("\n") if line.strip()]


def _notion_company(doc: BeautifulSoup, url: str) -> str | None:
    # Prefer topbar breadcrumb first page-block for canonical casing
    topbar = doc.select_one(".notion-topbar")
    if topbar:
        page_block = topbar.select_one(".notion-page-block")
        if page_block and (t := _text(page_block)):
            # "ParadeDB Job Board" → strip trailing " Job Board" / " Careers" etc.
            name = re.sub(
                r"\s+(Job Board|Careers?|Jobs?|Opportunities)\s*$", "", t, flags=re.IGNORECASE
            )
            # "Roles @Closure" → "Closure"
            if "@" in name:
                name = name.rsplit("@", 1)[1]
            name = name.strip()
            if name:
                return name
    # Fallback: subdomain of notion.site URL
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www", "notion"):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _notion_property_value(doc: BeautifulSoup, prop: str) -> str | None:
    lines = _notion_text_lines(doc)
    try:
        idx = lines.index(prop)
    except ValueError:
        return None
    # Collect value lines until the next property name or page-content heading
    values: list[str] = []
    for line in lines[idx + 1 :]:
        if line in _NOTION_PROPERTY_NAMES or line in _NOTION_PROPERTY_HEADINGS:
            break
        values.append(line)
    return ", ".join(values) if values else None


def _notion_location_section(doc: BeautifulSoup) -> str | None:
    """Location listed as a "Location:" heading in the page body (no property table)."""
    lines = _notion_text_lines(doc)
    try:
        idx = lines.index("Location:")
    except ValueError:
        return None
    values: list[str] = []
    for line in lines[idx + 1 :]:
        if line.endswith(":"):
            break
        values.append(line)
    return ", ".join(values) if values else None


def _notion_location(doc: BeautifulSoup, url: str) -> str | None:
    return _notion_property_value(doc, "Location") or _notion_location_section(doc)


def _notion_role_type(doc: BeautifulSoup, url: str) -> str | None:
    raw = (_notion_property_value(doc, "Employment Type") or "").lower()
    if not raw:
        return _generic_role_type(doc, url)
    if "full" in raw:
        return "full-time"
    if "part" in raw:
        return "part-time"
    if "contract" in raw:
        return "contract"
    if "intern" in raw:
        return "internship"
    return None


def _notion_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".notion-page-content")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": _notion_company,
    "location": _notion_location,
    "role_type": _notion_role_type,
    "description": _notion_description,
}
