# ---------------------------------------------------------------------------
# Middleware (middleware.io) — careers pages. The h1 is split across spans
# (whitespace needs collapsing), location is a "Location: X" paragraph in
# .job-details.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

HOSTNAME = "middleware.io"


def _middleware_title(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    return " ".join(h1.get_text(" ", strip=True).split()) or None


def _middleware_location(doc: BeautifulSoup, url: str) -> str | None:
    for p in doc.select(".job-details p"):
        text = p.get_text(" ", strip=True)
        if text.lower().startswith("location:"):
            return text.split(":", 1)[1].strip() or None
    return None


ADAPTER: dict[str, Any] = {
    "title": _middleware_title,
    "company_name": lambda doc, url: "Middleware",
    "location": _middleware_location,
}
