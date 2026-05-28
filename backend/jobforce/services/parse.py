"""Deterministic job page parser — mirrors chrome-extension/content.js adapter architecture."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

_CITIES = [
    "san-francisco", "new-york", "london", "seattle",
    "remote", "boston", "chicago", "austin",
]


def slug_to_location(pathname: str) -> str | None:
    seg = pathname.rstrip("/").split("/")[-1] or ""
    hit = next((c for c in _CITIES if seg.endswith(c)), None)
    if not hit:
        return None
    return " ".join(w.capitalize() for w in hit.split("-"))


def _text(el: Tag | None) -> str | None:
    if el is None:
        return None
    t = (el.get_text(separator=" ") or "").strip()
    return t or None


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
    return _text(el)


def _generic_role_type(doc: BeautifulSoup, url: str) -> str | None:
    body = doc.body
    t = (body.get_text() if body else "").lower()
    if "full-time" in t or "full time" in t:
        return "full-time"
    if "part-time" in t or "part time" in t:
        return "part-time"
    if "contract" in t:
        return "contract"
    if "internship" in t or "intern" in t:
        return "internship"
    return None


GENERIC_ADAPTER: dict[str, Any] = {
    "title": _generic_title,
    "company_name": _generic_company,
    "location": _generic_location,
    "description": _generic_description,
    "role_type": _generic_role_type,
}

# ---------------------------------------------------------------------------
# OpenAI site adapter — equivalent to openaiAdapter in content.js
# ---------------------------------------------------------------------------

def _openai_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main h2 + p, main h2 ~ p")
    if el and (t := _text(el)):
        return t
    return slug_to_location(urlparse(url).path)


def _openai_compensation(doc: BeautifulSoup, url: str) -> str | None:
    for el in doc.select("main p"):
        t = (el.get_text() or "").strip()
        if t.startswith("$"):
            return t
    return None


SITE_ADAPTERS: dict[str, dict[str, Any]] = {
    "openai.com": {
        "company_name": lambda doc, url: "OpenAI",
        "title": lambda doc, url: _text(doc.select_one("main h2")),
        "location": _openai_location,
        "description": lambda doc, url: _text(doc.select_one("main article, main section, main div")),
        "compensation": _openai_compensation,
    },
}

# ---------------------------------------------------------------------------
# Framework
# ---------------------------------------------------------------------------

def run_adapter(adapter: dict[str, Any], doc: BeautifulSoup, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, fn in adapter.items():
        try:
            result[key] = fn(doc, url)
        except Exception:
            logger.warning("[parse] adapter field %r error", key, exc_info=True)
            result[key] = None
    return result


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if v is not None and v != "":
            out[k] = v
    return out


def parse_html(html: str, url: str) -> dict[str, Any]:
    doc = BeautifulSoup(html, "lxml")
    hostname = urlparse(url).hostname or ""
    hostname = hostname.removeprefix("www.")
    adapter = SITE_ADAPTERS.get(hostname, {})
    base = run_adapter(GENERIC_ADAPTER, doc, url)
    override = run_adapter(adapter, doc, url) if adapter else {}
    return {"source_url": url, **merge(base, override)}
