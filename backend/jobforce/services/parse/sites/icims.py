# ---------------------------------------------------------------------------
# iCIMS (*.icims.com) — the real job content only exists inside a same-origin
# iframe on every iCIMS job page, even the "canonical" (non-iframe) URL; the
# wrapper page itself is a branded shell with nav chrome only. scout_fetch.py
# (`_extract_icims_frame_html`) merges the wrapper's <head> with the iframe's
# `.iCIMS_JobContainer` before this adapter ever runs, so title and
# company_name already resolve correctly via GENERIC_ADAPTER (h1, and the
# wrapper's clean og:site_name meta tag — the iframe's own og:site_name is
# just the generic literal "careers"). This adapter only covers location and
# description.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "icims.com"


def _icims_location(doc: BeautifulSoup, url: str) -> str | None:
    container = doc.select_one(".header.left")
    if container is None:
        return None
    spans = [s for s in container.find_all("span") if "sr-only" not in (s.get("class") or [])]
    return _text(spans[0]) if spans else None


def _icims_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".iCIMS_JobContent"))


ADAPTER: dict[str, Any] = {
    "location": _icims_location,
    "description": _icims_description,
}
