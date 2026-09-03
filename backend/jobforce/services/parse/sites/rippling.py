# ---------------------------------------------------------------------------
# Rippling ATS (ats.rippling.com/<company-slug>/jobs/<id>) — shared job board
# used by many companies. The recruiter-authored description sometimes
# embeds the next section's heading inside the same <h1> as the job title
# (via a nested <strong>), so title comes from the document <title> tag
# instead. There's no structured company-name field on the page; it's
# derived from the breadcrumb link back to the employer's own careers site
# (may need casing fixes via merge_companies after ingest).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "ats.rippling.com"


def _rippling_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.title) if doc.title else None


def _rippling_company(doc: BeautifulSoup, url: str) -> str | None:
    breadcrumb = doc.select_one('a[data-testid^="http"]')
    if breadcrumb is None:
        return None
    href = breadcrumb.get("data-testid") or ""
    host = (urlparse(str(href)).hostname or "").removeprefix("www.")
    label = host.split(".")[0]
    return label.replace("-", " ").title() or None


def _rippling_location(doc: BeautifulSoup, url: str) -> str | None:
    icon = doc.select_one('span[data-icon="LOCATION_OUTLINE"]')
    if icon is None:
        return None
    return _text(icon.find_next_sibling("p"))


def _rippling_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".ATS_htmlPreview"))


ADAPTER: dict[str, Any] = {
    "title": _rippling_title,
    "company_name": _rippling_company,
    "location": _rippling_location,
    "description": _rippling_description,
}
