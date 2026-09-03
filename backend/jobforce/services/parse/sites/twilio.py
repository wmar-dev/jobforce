# ---------------------------------------------------------------------------
# Twilio (jobs.twilio.com) — Eightfold-powered ATS hosted on Twilio's own
# domain. The static <h1> always reads "Single Position" no matter which job
# is loaded; the real title is in an <h2> further down (CSS-module class
# names are hashed per build, so match on the stable prefix instead).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "jobs.twilio.com"


def _twilio_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('h2[class*="position-title"]'))


def _twilio_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('div[class*="position-location"]'))


def _twilio_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("#job-description-container"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Twilio",
    "title": _twilio_title,
    "location": _twilio_location,
    "description": _twilio_description,
}
