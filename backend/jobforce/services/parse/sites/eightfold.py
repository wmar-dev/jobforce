# ---------------------------------------------------------------------------
# Eightfold (*.eightfold.ai) — same underlying ATS as jobs.twilio.com /
# apply.careers.microsoft.com (see sites/twilio.py), but on tenants' own
# eightfold.ai subdomains. The static <h1> always reads "Single Position"
# regardless of which job is loaded; the real title is a hashed-class <h2>
# further down. Unlike Twilio's layout, the job body sits behind a "Job
# Description" tab that scout_fetch.py clicks before capture (see
# `_TAB_CLICK_HOSTS`), after which it lands in the same
# #job-description-container id Twilio uses. Multi-tenant, so company_name
# has no fixed value — parse it from the "<Job Title> | <Company>" <title>
# tag instead (no stable company element/meta exists in the DOM).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown, normalize_posted_at

# careers.qualcomm.com is an Eightfold tenant on its own domain (same DOM).
HOSTNAMES = ["eightfold.ai", "careers.qualcomm.com"]


def _eightfold_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('h2[class*="position-title"]'))


def _eightfold_company(doc: BeautifulSoup, url: str) -> str | None:
    title_tag = doc.find("title")
    if title_tag is None:
        return None
    raw = (title_tag.get_text() or "").strip()
    if "|" not in raw:
        return None
    return raw.rsplit("|", 1)[-1].strip() or None


def _eightfold_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('div[class*="position-location"]'))


def _eightfold_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("#job-description-container"))


def _eightfold_posted_at(doc: BeautifulSoup, url: str) -> str | None:
    # CSS-module class names are hashed per build; anchor on the "Date
    # Posted" label text and read its sibling <dd> instead.
    label = doc.find("dt", string="Date Posted")
    if label is None:
        return None
    return normalize_posted_at(_text(label.find_next_sibling("dd")))


ADAPTER: dict[str, Any] = {
    "title": _eightfold_title,
    "company_name": _eightfold_company,
    "location": _eightfold_location,
    "description": _eightfold_description,
    "posted_at": _eightfold_posted_at,
}
