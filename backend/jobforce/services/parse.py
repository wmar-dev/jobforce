"""Deterministic job page parser — mirrors chrome-extension/content.js adapter architecture."""

from __future__ import annotations

import logging
import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

logger = logging.getLogger(__name__)

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
    # Use word boundary to avoid matching "contractor" / "government contractor"
    if re.search(r"\bcontract\b", t):
        return "contract"
    if re.search(r"\bintern(ship)?\b", t):
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
    # First h2 in main is the job title; its next sibling p is the dept/location line
    title_h2 = doc.select_one("main h2")
    if title_h2:
        el = title_h2.find_next_sibling("p")
        if el and (t := _text(el)):
            return t
    return slug_to_location(urlparse(url).path)


def _openai_compensation(doc: BeautifulSoup, url: str) -> str | None:
    for el in doc.select("main p"):
        t = (el.get_text() or "").strip()
        if t.startswith("$"):
            return t
    return None


def _greenhouse_company(doc: BeautifulSoup, url: str) -> str | None:
    # boards.greenhouse.io/<company>/jobs/<id> — extract from path
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 1 and parts[0] not in ("jobs",):
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _greenhouse_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job__location")
    return _text(el)


# ---------------------------------------------------------------------------
# Workday site adapter — myworkdayjobs.com
# URL: <company>.wd1.myworkdayjobs.com/en-US/<tenant>/job/<location>/<title>_<id>
# ---------------------------------------------------------------------------


def _workday_company(doc: BeautifulSoup, url: str) -> str | None:
    # Extract company from subdomain: acme.wd1.myworkdayjobs.com → Acme
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www",):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _workday_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='jobPostingTitle']")
    return _text(el)


def _workday_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='location']")
    return _text(el)


def _workday_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='job-posting-details']")
    return _text(el)


# ---------------------------------------------------------------------------
# Ashby site adapter — jobs.ashbyhq.com
# URL: jobs.ashbyhq.com/<company>/<job-id>
# ---------------------------------------------------------------------------


def _ashby_company(doc: BeautifulSoup, url: str) -> str | None:
    # Extract company from URL path: jobs.ashbyhq.com/figma/... → Figma
    parts = urlparse(url).path.strip("/").split("/")
    if parts and parts[0]:
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _ashby_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ashby-job-posting-heading, .ashby-job-posting-brief-description h1")
    return _text(el)


def _ashby_location(doc: BeautifulSoup, url: str) -> str | None:
    # Current markup: left pane has <h2>Location</h2><p>San Francisco</p> sections
    for section in doc.select(".ashby-job-posting-left-pane ._section_101oc_37, .ashby-job-posting-left-pane [class*='_section']"):
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
    return _text(el)


# ---------------------------------------------------------------------------
# Databricks site adapter — databricks.com/company/careers/...
# ---------------------------------------------------------------------------


def _databricks_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1:
        sib = h1.find_next_sibling()
        if sib:
            # Remove the "Apply now" button text
            for btn in sib.find_all("button"):
                btn.decompose()
            return _text(sib)
    return None


def _databricks_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _text(el)


SITE_ADAPTERS: dict[str, dict[str, Any]] = {
    "openai.com": {
        "company_name": lambda doc, url: "OpenAI",
        "title": lambda doc, url: _text(doc.select_one("main h2")),
        "location": _openai_location,
        "description": lambda doc, url: _text(
            doc.select_one("main article, main section, main div")
        ),
        "compensation": _openai_compensation,
    },
    "boards.greenhouse.io": {
        "company_name": _greenhouse_company,
        "location": _greenhouse_location,
    },
    "job-boards.greenhouse.io": {
        "company_name": _greenhouse_company,
        "location": _greenhouse_location,
    },
    "myworkdayjobs.com": {
        "company_name": _workday_company,
        "title": _workday_title,
        "location": _workday_location,
        "description": _workday_description,
    },
    "jobs.ashbyhq.com": {
        "company_name": _ashby_company,
        "title": _ashby_title,
        "location": _ashby_location,
        "description": _ashby_description,
    },
    "databricks.com": {
        "company_name": lambda doc, url: "Databricks",
        "location": _databricks_location,
        "description": _databricks_description,
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


def _match_adapter(hostname: str) -> dict[str, Any]:
    if hostname in SITE_ADAPTERS:
        return SITE_ADAPTERS[hostname]
    # suffix match for subdomain-based ATSes (e.g. acme.wd1.myworkdayjobs.com)
    for key, adapter in SITE_ADAPTERS.items():
        if hostname.endswith("." + key):
            return adapter
    return {}


def parse_html(html: str, url: str) -> dict[str, Any]:
    doc = BeautifulSoup(html, "lxml")
    hostname = urlparse(url).hostname or ""
    hostname = hostname.removeprefix("www.")
    adapter = _match_adapter(hostname)
    base = run_adapter(GENERIC_ADAPTER, doc, url)
    override = run_adapter(adapter, doc, url) if adapter else {}
    return {"source_url": url, **merge(base, override)}
