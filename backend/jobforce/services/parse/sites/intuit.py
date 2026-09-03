# ---------------------------------------------------------------------------
# Intuit (jobs.intuit.com) — shared board across all Intuit brands (Credit
# Karma, TurboTax, QuickBooks, Mailchimp). Title extracts fine via the
# generic adapter's <h1>, which carries a " - <Brand>" suffix for brand
# postings — but the same " - <suffix>" shape also shows up for team/domain
# suffixes ("Staff Software Engineer - Back End") and initiative prefixes
# ("Fintech Futures - Senior Staff Software Engineer") that are NOT brands.
# Only treat the suffix as company_name when it matches a known brand;
# default to "Intuit" otherwise. The generic adapter's location falls back
# to page-level "Multiple Locations" metadata instead of the real
# ".job-location-jd" element.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "jobs.intuit.com"

_KNOWN_BRANDS = {"Credit Karma", "TurboTax", "QuickBooks", "Mailchimp", "Mint"}


def _intuit_company(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    text = _text(h1) or ""
    if " - " in text:
        suffix = text.rsplit(" - ", 1)[-1].strip()
        if suffix in _KNOWN_BRANDS:
            return suffix
    return "Intuit"


def _intuit_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job-location-jd")
    if el is None:
        return None
    text = _text(el) or ""
    text = re.sub(r"^Location\s*", "", text)
    text = re.sub(r"\s*;\s*", "; ", text)
    return text.strip() or None


ADAPTER: dict[str, Any] = {
    "company_name": _intuit_company,
    "location": _intuit_location,
}
