# ---------------------------------------------------------------------------
# Workday site adapter — myworkdayjobs.com
# URL: <company>.wd1.myworkdayjobs.com/en-US/<tenant>/job/<location>/<title>_<id>
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "myworkdayjobs.com"


def _workday_company(doc: BeautifulSoup, url: str) -> str | None:
    # Extract company from subdomain: acme.wd1.myworkdayjobs.com → Acme
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www",):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _workday_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='jobPostingTitle']")
    if t := _text(el):
        return t
    # Some Workday tenants don't render the nested jobPostingTitle element and
    # only have the job title text directly in the jobPostingHeader heading.
    return _text(doc.select_one("[data-automation-id='jobPostingHeader']"))


def _workday_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='location']")
    if t := _text(el):
        return t
    # Some Workday tenants render locations as a <dl><dt>locations</dt><dd>...</dd>...</dl>
    # list (one <dd> per location) instead of a single nested "location" element.
    dds = doc.select("[data-automation-id='locations'] dd")
    if dds:
        return "; ".join(t for dd in dds if (t := _text(dd)))
    return None


def _workday_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("[data-automation-id='job-posting-details']")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": _workday_company,
    "title": _workday_title,
    "location": _workday_location,
    "description": _workday_description,
}
