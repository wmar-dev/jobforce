# ---------------------------------------------------------------------------
# Discord (discord.com/jobs/<id>) — custom React SPA
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "discord.com"


def _discord_location(doc: BeautifulSoup, url: str) -> str | None:
    # Location lives in a div with class containing "heroLocation"
    el = doc.select_one('[class*="heroLocation"]')
    return _text(el)


def _discord_description(doc: BeautifulSoup, url: str) -> str | None:
    # Job body container has class "body-" and "section-" and "document-"
    el = doc.select_one('[class*="body-"][class*="section-"]')
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Discord",
    "location": _discord_location,
    "description": _discord_description,
}
