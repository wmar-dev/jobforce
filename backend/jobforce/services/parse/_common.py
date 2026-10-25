"""Shared helpers plus the generic/fallback adapter used by every site module."""

from __future__ import annotations

import html as html_module
import json
import re
from datetime import datetime
from typing import Any

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify as md

_CITIES = [
    "san-francisco",
    "new-york",
    "london",
    "seattle",
    "remote",
    "boston",
    "chicago",
    "austin",
]


def slug_to_location(pathname: str) -> str | None:
    seg = pathname.rstrip("/").split("/")[-1] or ""
    # Check suffix match first (e.g. "...-san-francisco")
    hit = next((c for c in _CITIES if seg.endswith(c)), None)
    if not hit:
        # Also match city anywhere in slug (e.g. "...-remote-us")
        hit = next((c for c in _CITIES if f"-{c}-" in seg or seg.startswith(f"{c}-")), None)
    if not hit:
        return None
    return " ".join(w.capitalize() for w in hit.split("-"))


def _text(el: Tag | None) -> str | None:
    if el is None:
        return None
    t = (el.get_text(separator=" ") or "").strip()
    return t or None


def _to_markdown(el: Tag | None) -> str | None:
    if el is None:
        return None
    result = md(str(el), heading_style="ATX", bullets="-", strip=["a", "img"]).strip()
    return result or None


_HTML_TAG_RE = re.compile(r"<[a-zA-Z][^>]*>")


def normalize_description(description: str | None) -> str | None:
    """Guard against HTML-entity-escaped markup landing in `description` verbatim.

    Some ingest sources (e.g. an ATS JSON API's rich-text field) hand back
    HTML pre-escaped for embedding — a raw copy shows up as literal
    `&lt;div&gt;` text instead of rendered content. Unescape, and if that
    reveals real HTML tags, convert to markdown so storage stays consistent
    with the normal parse_html path.
    """
    if description is None:
        return None
    unescaped = html_module.unescape(description)
    if _HTML_TAG_RE.search(unescaped):
        result = md(unescaped, heading_style="ATX", bullets="-", strip=["a", "img"]).strip()
        return result or None
    return unescaped.strip() or None


_POSTED_AT_FORMATS = (
    "%B %d, %Y",  # "September 20, 2026" (Eightfold)
    "%b %d, %Y",  # "Sep 20, 2026"
)


def normalize_posted_at(raw: str | None) -> str | None:
    """Coerce a site's "date posted" text to a plain ISO date (YYYY-MM-DD).

    Sources hand this back in wildly different shapes — ISO datetimes
    ("2026-08-11T06:02:43.000Z"), bare ISO dates ("2026-08-28"), or
    human-readable text ("September 20, 2026"). Storing whatever a site
    happens to use verbatim would make `posted_at` unsortable/unfilterable
    as plain text (e.g. "September ..." sorts alphabetically, not
    chronologically, against "2026-08-28"), so every adapter normalizes
    through here rather than returning raw source text directly.
    """
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date().isoformat()
    except ValueError:
        pass
    for fmt in _POSTED_AT_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def find_jobposting_jsonld(doc: BeautifulSoup) -> dict[str, Any] | None:
    """Return the first schema.org JobPosting JSON-LD block on the page, if any.

    Widely used across ATS platforms (Teamtailor, Jobvite, Kula, and many
    custom career sites) for SEO — shared here so both the generic adapter
    and site-specific ones can pull fields (title, description, datePosted,
    jobLocation, hiringOrganization, ...) from it without each re-parsing it.
    """
    for script in doc.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except ValueError:
            continue
        if isinstance(data, dict) and data.get("@type") == "JobPosting":
            return data
    return None


# ---------------------------------------------------------------------------
# Generic adapter — equivalent to genericAdapter in content.js
# ---------------------------------------------------------------------------


def _generic_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("h1")
    if el and (t := _text(el)):
        return t
    title_tag = doc.find("title")
    if title_tag:
        raw = (title_tag.get_text() or "").strip()
        return re.sub(r"\s*[-|].*$", "", raw).strip() or None
    return None


def _generic_company(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-company], .company-name, .employer-name")
    if el and (t := _text(el)):
        return t
    meta = doc.find("meta", attrs={"property": "og:site_name"})
    if meta:
        return (meta.get("content") or "").strip() or None  # type: ignore[union-attr]
    return None


def _generic_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-location], .job-location, .location")
    if el and (t := _text(el)):
        return t
    meta = doc.find("meta", attrs={"name": "job:location"})
    if meta:
        return (meta.get("content") or "").strip() or None  # type: ignore[union-attr]
    return None


def _generic_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[class*="description"], [class*="job-desc"], #job-description')
    return _to_markdown(el)


def _generic_role_type(doc: BeautifulSoup, url: str) -> str | None:
    body = doc.body
    t = (body.get_text() if body else "").lower()
    if "full-time" in t or "full time" in t:
        return "full-time"
    if "part-time" in t or "part time" in t:
        return "part-time"
    # Use word boundary to avoid matching "contractor" / "government contractor"
    if re.search(r"\bcontract\b", t):
        return "contract"
    # Skip "non-internship experience" requirements (common Amazon boilerplate)
    if re.search(r"(?<!non-)(?<!non )\bintern(ship)?\b", t):
        return "internship"
    return None


def _generic_posted_at(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc)
    if data is not None:
        posted = data.get("datePosted")
        if isinstance(posted, str) and (normalized := normalize_posted_at(posted)):
            return normalized
    meta = doc.find("meta", attrs={"itemprop": "datePosted"}) or doc.find(
        "meta", attrs={"property": "article:published_time"}
    )
    if meta:
        content = meta.get("content")
        if isinstance(content, str) and (normalized := normalize_posted_at(content)):
            return normalized
    return None


GENERIC_ADAPTER: dict[str, Any] = {
    "title": _generic_title,
    "company_name": _generic_company,
    "location": _generic_location,
    "description": _generic_description,
    "role_type": _generic_role_type,
    "posted_at": _generic_posted_at,
}
