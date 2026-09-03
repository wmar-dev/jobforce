# ---------------------------------------------------------------------------
# TikTok / lifeattiktok.com site adapter
# Detail page structure (React SPA, CSS-Module class names):
#   .job-header > [data-test="jobTitle"]         = job title
#   .job-info   > span[0] > span.clamp-content   = location (e.g. "San Jose")
#   .job-info   > span[1]                        = employment type ("Regular" = full-time)
#   .block-title / .block-content pairs          = description sections
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _generic_role_type, _text, _to_markdown

HOSTNAME = "lifeattiktok.com"


def _tiktok_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('[data-test="jobTitle"]'))


def _tiktok_location(doc: BeautifulSoup, url: str) -> str | None:
    job_info = doc.select_one(".job-info")
    if not job_info:
        return None
    for span in job_info.find_all("span", recursive=False):
        if t := _text(span):
            return t
    return None


def _tiktok_role_type(doc: BeautifulSoup, url: str) -> str | None:
    job_info = doc.select_one(".job-info")
    if job_info:
        spans = [s for s in job_info.find_all("span", recursive=False) if _text(s)]
        if len(spans) >= 2:
            raw = (_text(spans[1]) or "").lower()
            if "regular" in raw:
                return "full-time"
            if "intern" in raw:
                return "internship"
            if "contract" in raw:
                return "contract"
    return _generic_role_type(doc, url)


def _tiktok_description(doc: BeautifulSoup, url: str) -> str | None:
    parts: list[str] = []
    for el in doc.select(".block-title, .block-content"):
        classes = el.get_attribute_list("class")
        if "block-title" in classes:
            parts.append(f"\n## {_text(el)}\n")
        elif "block-content" in classes:
            if md_part := _to_markdown(el):
                parts.append(md_part)
    return "\n".join(parts).strip() or None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "TikTok",
    "title": _tiktok_title,
    "location": _tiktok_location,
    "role_type": _tiktok_role_type,
    "description": _tiktok_description,
}
