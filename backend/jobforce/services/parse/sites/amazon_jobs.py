# ---------------------------------------------------------------------------
# Amazon.jobs (amazon.jobs) — React SPA. Location is in the "Job details"
# sidebar association list (older pages: a ".location" div holding a bold
# "Location:" label followed by the text). The body is a set of
# ".section" blocks (h2 + content) under "#job-detail-body".
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "amazon.jobs"


def _amazon_jobs_location(doc: BeautifulSoup, url: str) -> str | None:
    # Newer layout: "Job details" sidebar, one <li> per location
    items = [
        t
        for li in doc.select("div.association.location-icon ul.association-content li")
        if (t := _text(li))
    ]
    if items:
        return "; ".join(items)
    text = _text(doc.select_one("div.location"))
    if not text:
        return None
    return text.removeprefix("Location:").strip() or None


def _amazon_jobs_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [md for el in doc.select("#job-detail-body .section") if (md := _to_markdown(el))]
    return "\n\n".join(parts) if parts else None


def _amazon_jobs_role_type(doc: BeautifulSoup, url: str) -> str | None:
    # The generic whole-page scan misfires here: a "Recommended jobs" widget lists
    # intern postings, and descriptions say "non-internship" / "API contract".
    # Amazon intern postings always say so in the title; everything else is
    # full-time (returning None would let the generic scan win).
    title = _text(doc.select_one("h1.title")) or ""
    return "internship" if re.search(r"\bintern(ship)?\b", title, re.I) else "full-time"


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Amazon",
    "location": _amazon_jobs_location,
    "role_type": _amazon_jobs_role_type,
    "description": _amazon_jobs_description,
}
