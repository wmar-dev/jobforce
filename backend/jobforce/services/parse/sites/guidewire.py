# ---------------------------------------------------------------------------
# Guidewire (guidewire.com/about/careers/jobs/<slug>) — title extracts fine
# via the generic adapter (no <h1>; the page uses <h2> for the job title, so
# the generic adapter falls back to the <title> tag); location and
# description aren't exposed via any plain element the generic adapter
# checks — its description fallback picks up the site's footer boilerplate
# ("We do not accept bot-generated candidate applications...") instead.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "guidewire.com"


def _guidewire_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".JobDetail_heroTitle__48mry"))


def _guidewire_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".JobDetail_heroLocation__aqxLv"))


def _guidewire_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".JobDetail_contentSection__XzJan"))


ADAPTER: dict[str, Any] = {
    "title": _guidewire_title,
    "location": _guidewire_location,
    "description": _guidewire_description,
}
