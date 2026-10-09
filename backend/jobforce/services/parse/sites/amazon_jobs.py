# ---------------------------------------------------------------------------
# Amazon.jobs (amazon.jobs) — React SPA. Location is a ".location" div holding
# a bold "Location:" label followed by the text. The body is a set of
# ".section" blocks (h2 + content) under "#job-detail-body".
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "amazon.jobs"


def _amazon_jobs_location(doc: BeautifulSoup, url: str) -> str | None:
    text = _text(doc.select_one("div.location"))
    if not text:
        return None
    return text.removeprefix("Location:").strip() or None


def _amazon_jobs_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [md for el in doc.select("#job-detail-body .section") if (md := _to_markdown(el))]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Amazon",
    "location": _amazon_jobs_location,
    "description": _amazon_jobs_description,
}
