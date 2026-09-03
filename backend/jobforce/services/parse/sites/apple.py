# ---------------------------------------------------------------------------
# Apple site adapter — jobs.apple.com/en-us/details/<id>/<slug>
# Page structure: h1 = job title (generic handles this). Location and team
# are sibling <label> elements (#jobdetails-joblocation / #jobdetails-teamname)
# in the row right after the h1. Job content is split across sibling
# div#jobdetails-* sections (Summary, Description, Responsibilities,
# Qualifications, Pay & Benefits, plus unheaded legal-boilerplate footers);
# only the headed sections are joined for the description.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "jobs.apple.com"


def _apple_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("#jobdetails-joblocation"))


def _apple_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = []
    for div in doc.select("section.hyperlink-underline > div[id^='jobdetails-']"):
        if div.find("h2") and (md_text := _to_markdown(div)):
            parts.append(md_text)
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Apple",
    "location": _apple_location,
    "description": _apple_description,
}
