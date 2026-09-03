# ---------------------------------------------------------------------------
# Intuit (jobs.intuit.com) — shared board across all Intuit brands (Credit
# Karma, TurboTax, QuickBooks, Mailchimp). Title extracts fine via the
# generic adapter's <h1>, which carries a " - <Brand>" suffix company_name is
# derived from (falls back to "Intuit" for postings with no such suffix).
# The generic adapter's location falls back to page-level "Multiple
# Locations" metadata instead of the real ".job-location-jd" element.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "jobs.intuit.com"


def _intuit_company(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    text = _text(h1) or ""
    if " - " in text:
        return text.rsplit(" - ", 1)[-1].strip() or "Intuit"
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
