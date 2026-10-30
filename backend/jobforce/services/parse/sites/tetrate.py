# ---------------------------------------------------------------------------
# Tetrate (careers.tetr8.io) — Astro static page. The h1 title and the job
# body (p / h2 / ul blocks) are siblings inside one Tailwind flex column; the
# apply form lives in a separate sibling column. Location is not a structured
# field — it's a trailing "<strong>Location:</strong> ..." prose paragraph
# (typically "fully distributed ... North American time zone").
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "careers.tetr8.io"

_LOCATION_LABEL_RE = re.compile(r"^\s*Location\s*:\s*", re.IGNORECASE)
_REMOTE_RE = re.compile(r"fully distributed|remote|from anywhere", re.IGNORECASE)
_NORTH_AMERICA_RE = re.compile(r"North America", re.IGNORECASE)


def _location_paragraph(doc: BeautifulSoup) -> Tag | None:
    for strong in doc.select("p > strong"):
        if _LOCATION_LABEL_RE.match(strong.get_text()):
            parent = strong.parent
            return parent if isinstance(parent, Tag) else None
    return None


def _tetrate_location(doc: BeautifulSoup, url: str) -> str | None:
    para = _location_paragraph(doc)
    raw = _text(para)
    if not raw:
        return None
    text = " ".join(_LOCATION_LABEL_RE.sub("", raw).split())
    if not text:
        return None
    if _REMOTE_RE.search(text):
        return "Remote (North America)" if _NORTH_AMERICA_RE.search(text) else "Remote"
    return text


def _tetrate_description(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if not h1:
        return None
    parts = [
        md
        for sib in h1.find_next_siblings()
        if isinstance(sib, Tag) and sib.name not in ("script", "style", "button")
        if (md := _to_markdown(sib))
    ]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Tetrate",
    "location": _tetrate_location,
    "description": _tetrate_description,
}
