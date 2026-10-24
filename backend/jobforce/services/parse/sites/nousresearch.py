# ---------------------------------------------------------------------------
# Nous Research (nousresearch.com) — Next.js catalogue page. The eyebrow
# <p> holds "Full time, Remote"-style metadata, the <h1> holds the title,
# and the body is an intro paragraph plus <section> blocks.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "nousresearch.com"

_EMPLOYMENT_TYPES = {"full time", "part time", "contract", "intern", "internship"}


def _nous_title(doc: BeautifulSoup, url: str) -> str | None:
    # The <h1> repeats its text in an aria-hidden span for the animation.
    return _text(doc.select_one(".nw-catalogue-title > span:not([aria-hidden])"))


def _nous_location(doc: BeautifulSoup, url: str) -> str | None:
    eyebrow = _text(doc.select_one(".nw-catalogue-eyebrow"))
    if not eyebrow:
        return None
    parts = [p.strip() for p in eyebrow.split(",")]
    places = [p for p in parts if p and p.lower() not in _EMPLOYMENT_TYPES]
    return ", ".join(places) or None


def _nous_description(doc: BeautifulSoup, url: str) -> str | None:
    els = doc.select(".nw-career-intro, section.nw-catalogue-section")
    parts = [md for el in els if (md := _to_markdown(el))]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Nous Research",
    "title": _nous_title,
    "location": _nous_location,
    "description": _nous_description,
}
