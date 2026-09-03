# ---------------------------------------------------------------------------
# Palo Alto Networks (jobs.paloaltonetworks.com) — a section-based CMS
# template (numbered "sectionNN" blocks). The page has a marketing hero
# `h1.section26__heading` ("Revolutionizing protection.") ahead of the real
# job title, which lives in `h2.section30__job-title` — the generic
# adapter's bare "h1" selector grabs the hero instead. There's no
# `og:site_name` (or any company element) on this template; this domain
# only ever serves Palo Alto Networks postings, so company_name is a fixed
# value. location sits in `span.section30__job-info-location`, which the
# generic adapter's `[data-location], .job-location, .location` selectors
# don't match. description: the generic adapter's `[class*="description"]`
# selector matches the outer `<section class="job-description ...">`
# wrapper — which also holds the title, location, Ref ID, Apply button, and
# "Current Employees" boilerplate — instead of the inner `.ats-description`
# div that holds just the real job body, so description is pointed there
# directly.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "jobs.paloaltonetworks.com"


def _paloaltonetworks_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h2.section30__job-title"))


def _paloaltonetworks_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".section30__job-info-location"))


def _paloaltonetworks_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".ats-description"))


ADAPTER: dict[str, Any] = {
    "title": _paloaltonetworks_title,
    "company_name": lambda doc, url: "Palo Alto Networks",
    "location": _paloaltonetworks_location,
    "description": _paloaltonetworks_description,
}
