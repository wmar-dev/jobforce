# ---------------------------------------------------------------------------
# Bowser AI (bowserai.com) — static job pages. ".header" holds ".company", the
# h1 title and ".meta" ("<location> · <type> · <team>"); the body is a series
# of ".section" blocks.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "bowserai.com"


def _bowserai_company(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".header .company")) or "Bowser AI"


def _bowserai_location(doc: BeautifulSoup, url: str) -> str | None:
    meta = _text(doc.select_one(".header .meta"))
    if not meta:
        return None
    return meta.split("·")[0].strip() or None


def _bowserai_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [md for el in doc.select(".section") if (md := _to_markdown(el))]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": _bowserai_company,
    "location": _bowserai_location,
    "description": _bowserai_description,
}
