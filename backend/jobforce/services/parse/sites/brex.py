# ---------------------------------------------------------------------------
# Brex (brex.com/careers/<id>) — title and company_name already extract
# correctly via the generic adapter. Brex renders Greenhouse's job content
# HTML directly, including its ".content-intro" wrapper div, so the
# description container is that div's parent.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "brex.com"


def _brex_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h4"))


def _brex_description(doc: BeautifulSoup, url: str) -> str | None:
    intro = doc.select_one(".content-intro")
    if intro is None:
        return None
    container = intro.find_parent("div")
    return _to_markdown(container)


ADAPTER: dict[str, Any] = {
    "location": _brex_location,
    "description": _brex_description,
}
