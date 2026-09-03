# ---------------------------------------------------------------------------
# Atlassian (atlassian.com) — custom careers CMS. Title/company_name already
# extract correctly via the generic adapter (h1 / og:site_name). Location
# lives in a pipe-separated ".job-posting-detail--highlight" paragraph
# ("Team | City, Country[ or Remote] | Remote flag"); description is the
# first ".column.colspan-10.text-left" div inside the job-posting-detail
# section (a second, empty one immediately follows it, so select_one's
# document-order match picks the right one).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "atlassian.com"


def _atlassian_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job-posting-detail--highlight")
    text = _text(el)
    if not text:
        return None
    parts = [p.strip() for p in text.split("|") if p.strip()]
    # Format: "Team | City, Country[ or Remote] | Remote, Remote" — location
    # is the middle segment.
    if len(parts) >= 2:
        return parts[1]
    return None


def _atlassian_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("section.job-posting-detail .column.colspan-10.text-left")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "location": _atlassian_location,
    "description": _atlassian_description,
}
