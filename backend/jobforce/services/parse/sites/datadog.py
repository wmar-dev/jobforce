# ---------------------------------------------------------------------------
# Datadog careers (careers.datadoghq.com) — a client-rendered React app.
# The job title lives in an unclassed `<h2>` (not `<h1>`), so the generic
# adapter's `h1` selector misses it and falls back to the `<title>` tag,
# which the trailing-segment regex truncates at the first "-" (dropping
# everything after "Staff Software Engineer" in e.g. "Staff Software
# Engineer - Corporate Development | Datadog Careers"). Location is a plain
# unclassed `<p>` in the `<div>` immediately after the `<h2>` — no
# ".location"/"[data-location]" match for the generic adapter. og:site_name
# is "Datadog Careers | Datadog" rather than a clean company name, so
# company_name is hardcoded instead (same pattern as the Apple adapter).
# description already resolves via the generic adapter (a ".job-description"
# div is present).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "careers.datadoghq.com"


def _datadog_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("main h2"))


def _datadog_location(doc: BeautifulSoup, url: str) -> str | None:
    h2 = doc.select_one("main h2")
    if h2 is None:
        return None
    sibling = h2.find_next_sibling("div")
    return _text(sibling.select_one("p")) if sibling else None


ADAPTER: dict[str, Any] = {
    "title": _datadog_title,
    "company_name": lambda doc, url: "Datadog",
    "location": _datadog_location,
}
