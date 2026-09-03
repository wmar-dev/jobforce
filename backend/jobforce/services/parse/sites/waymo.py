# ---------------------------------------------------------------------------
# Waymo site adapter — careers.withwaymo.com/jobs/<slug>
# Generic "h1, main h2" selectors hit unrelated sitewide headings ("Working
# at Waymo", "Teams") before the real job title, and the generic
# [class*="location"] selector matches a related-job sidebar link instead of
# this job's own location. Title/location must be scoped to
# .block-job-description, which wraps just this job's own content.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "careers.withwaymo.com"


def _waymo_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".block-job-description h3.job-title"))


def _waymo_location(doc: BeautifulSoup, url: str) -> str | None:
    els = doc.select(".block-job-description .job-component-location")
    parts = [t for el in els if (t := _text(el))]
    return ", ".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Waymo",
    "title": _waymo_title,
    "location": _waymo_location,
}
