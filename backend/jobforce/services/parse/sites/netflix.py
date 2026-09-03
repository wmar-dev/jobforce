# ---------------------------------------------------------------------------
# Netflix (explore.jobs.netflix.net) — Eightfold-powered ATS hosted on
# Netflix's own domain. Title and description already extract correctly via
# the generic adapter (no hydration race observed on this board — the h1 and
# description container render with real content on first fetch). Two gaps:
# `og:site_name` reads "Careers at Netflix" rather than the company name, and
# the location paragraph carries a "+ N more" overflow link that needs
# stripping once the trailing locations are elided.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "explore.jobs.netflix.net"


def _netflix_location(doc: BeautifulSoup, url: str) -> str | None:
    raw = _text(doc.select_one("p.position-location"))
    if raw is None:
        return None
    cleaned = re.sub(r"\s*\+\s*\d+\s+more\s*$", "", raw)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned or None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Netflix",
    "location": _netflix_location,
}
