# ---------------------------------------------------------------------------
# Microsoft (apply.careers.microsoft.com) — same Eightfold-powered ATS as
# Twilio's board. The static <h1> always reads "Single Position" no matter
# which job is loaded; the real title is in an <h2> further down (CSS-module
# class names are hashed per build, so match on the stable prefix instead).
# The page never renders the company name as visible text, so it's fixed.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "apply.careers.microsoft.com"


def _microsoft_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('h2[class*="position-title"]'))


def _microsoft_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('div[class*="position-location"]'))


def _microsoft_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("#job-description-container"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Microsoft",
    "title": _microsoft_title,
    "location": _microsoft_location,
    "description": _microsoft_description,
}
