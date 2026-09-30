# ---------------------------------------------------------------------------
# Polymer-hosted careers pages (careers.honeyhive.ai/<id>, jobs.polymer.co/<company>/<id>)
# Page structure: header .job-header__company h1 (company)
#                 .job-details-intro h1.title (title) + ul.traits > li (department, job type, location)
#                 section.formatted-text (description)
# Note: traits are positional (department first); the location is the li that is neither
#       the department nor a job-type label.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAMES = ["careers.honeyhive.ai", "jobs.polymer.co"]

_JOB_TYPE_RE = re.compile(
    r"^(full|part)[- ]time$|^contract(or)?$|^intern(ship)?$|^temporary$", re.I
)


def _polymer_company(doc: BeautifulSoup, url: str) -> str | None:
    link = doc.select_one("a.job-header__company h1")
    return _text(link)


def _polymer_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h1.title"))


def _polymer_location(doc: BeautifulSoup, url: str) -> str | None:
    items = [_text(li) for li in doc.select("ul.traits li")]
    # First trait is the department; skip it and any job-type label.
    for item in items[1:]:
        if item and not _JOB_TYPE_RE.match(item):
            return item
    return None


def _polymer_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("section.formatted-text"))


ADAPTER: dict[str, Any] = {
    "company_name": _polymer_company,
    "title": _polymer_title,
    "location": _polymer_location,
    "description": _polymer_description,
}
