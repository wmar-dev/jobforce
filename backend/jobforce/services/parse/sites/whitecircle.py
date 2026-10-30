# ---------------------------------------------------------------------------
# White Circle (whitecircle.com) — Next.js/Tailwind careers page at
# /careers/<slug>-<uuid>. A "header#job-overview" card holds a row of chip
# spans (location first, then workplace type / team), the h1 title, and a
# summary paragraph; the body lives in "article.job-description".
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "whitecircle.com"


def _whitecircle_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("header#job-overview div.flex-wrap > span"))


def _whitecircle_description(doc: BeautifulSoup, url: str) -> str | None:
    parts: list[str] = []
    summary = doc.select_one("header#job-overview h1 ~ p")
    if summary_md := _to_markdown(summary):
        parts.append(summary_md)
    if body_md := _to_markdown(doc.select_one("article.job-description")):
        parts.append(body_md)
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "White Circle",
    "location": _whitecircle_location,
    "description": _whitecircle_description,
}
