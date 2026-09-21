# ---------------------------------------------------------------------------
# SmartRecruiters (jobs.smartrecruiters.com) — schema.org JobPosting microdata.
# The DOM also carries a hidden "IE11 no longer supported" overlay whose own
# <h1> precedes the real job-title <h1> in document order, so the generic
# adapter's bare `doc.select_one("h1")` picks the wrong one — anchor on
# h1.job-title instead. Location is rendered by a custom <spl-job-location>
# element with a formattedaddress attribute rather than text content.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "jobs.smartrecruiters.com"


def _smartrecruiters_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h1.job-title"))


def _smartrecruiters_company(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one('[itemprop="hiringOrganization"] meta[itemprop="name"]')
    if el:
        return (el.get("content") or "").strip() or None  # type: ignore[union-attr]
    return None


def _smartrecruiters_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("spl-job-location")
    if el and (addr := el.get("formattedaddress")):
        return str(addr).strip() or None
    return _text(doc.select_one('[itemprop="jobLocation"]'))


def _smartrecruiters_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one('[itemprop="description"]'))


ADAPTER: dict[str, Any] = {
    "title": _smartrecruiters_title,
    "company_name": _smartrecruiters_company,
    "location": _smartrecruiters_location,
    "description": _smartrecruiters_description,
}
