# ---------------------------------------------------------------------------
# Paylocity Recruiting (recruiting.paylocity.com) — the <title> tag reads
# "<Company> - <Job Title>", the reverse of the generic adapter's assumed
# "<Job Title> - <Company>" order, so its regex-stripped title comes back as
# the company name instead. There's no h1 at all; the visible job title is a
# plain <span class="job-preview-title">.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "recruiting.paylocity.com"


def _paylocity_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".job-preview-title"))


def _paylocity_company(doc: BeautifulSoup, url: str) -> str | None:
    title_tag = doc.find("title")
    if title_tag is None:
        return None
    raw = (title_tag.get_text() or "").strip()
    if " - " not in raw:
        return None
    return raw.split(" - ", 1)[0].strip() or None


def _paylocity_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".preview-location")
    if el is None:
        return None
    text = el.get_text(separator=" ")
    return " ".join(text.split()) or None


def _paylocity_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".job-preview-details"))


ADAPTER: dict[str, Any] = {
    "title": _paylocity_title,
    "company_name": _paylocity_company,
    "location": _paylocity_location,
    "description": _paylocity_description,
}
