# ---------------------------------------------------------------------------
# Skydio (skydio.com) — Greenhouse-backed careers pages rendered by Skydio's
# own site. The h1 title is followed by a "type-body-2" paragraph holding
# "<location>- <employment type>" and then a ".prose.block-content" div with
# the job body.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "skydio.com"

_EMPLOYMENT_SUFFIX = re.compile(
    r"\s*-\s*(Full[- ]time|Part[- ]time|Contract|Intern(ship)?)\s*$", re.I
)


def _skydio_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    para = h1.find_next_sibling("p") if h1 else None
    text = _text(para)
    if not text:
        return None
    return _EMPLOYMENT_SUFFIX.sub("", text) or None


def _skydio_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".prose.block-content"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Skydio",
    "location": _skydio_location,
    "description": _skydio_description,
}
