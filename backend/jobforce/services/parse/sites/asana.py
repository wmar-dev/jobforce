# ---------------------------------------------------------------------------
# Asana (asana.com/jobs/apply/<id>) — title already extracts correctly via
# the generic adapter's <h1> selector; company_name, location, and
# description need overrides since CSS-module class names are hashed per
# build. The description div is the sibling right after the div holding the
# "#grnhse_app" apply anchor (Asana embeds a Greenhouse apply widget there).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "asana.com"


def _asana_location(doc: BeautifulSoup, url: str) -> str | None:
    main = doc.select_one("main")
    return _text(main.select_one("h4")) if main else None


def _asana_description(doc: BeautifulSoup, url: str) -> str | None:
    apply_link = doc.select_one('a[href^="#grnhse_app"]')
    if apply_link is None:
        return None
    apply_container = apply_link.find_parent("div")
    if apply_container is None:
        return None
    desc_div = apply_container.find_next_sibling("div")
    return _to_markdown(desc_div)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Asana",
    "location": _asana_location,
    "description": _asana_description,
}
