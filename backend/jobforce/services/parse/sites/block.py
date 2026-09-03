# ---------------------------------------------------------------------------
# Block (block.xyz/careers/jobs/<id>) — the site's own og:site_name meta is
# buggy and echoes the page title instead of "Block", so the generic
# adapter's company_name fallback grabs the wrong text.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "block.xyz"


def _block_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one('[data-testid="job-location"]'))


def _block_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one('[data-testid="job-about"]'))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Block",
    "location": _block_location,
    "description": _block_description,
}
