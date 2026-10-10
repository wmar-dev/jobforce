# ---------------------------------------------------------------------------
# Subconscious (subconscious.dev) — Next.js careers pages with no JobPosting
# JSON-LD. The hero has a "Department · Location" paragraph under the h1; the
# job body is the Tailwind ".prose" block.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "subconscious.dev"


def _subconscious_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    for p in h1.find_next_siblings("p"):
        text = p.get_text(" ", strip=True)
        if "·" in text:
            return text.split("·", 1)[1].strip() or None
    return None


def _subconscious_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("div.prose"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Subconscious",
    "location": _subconscious_location,
    "description": _subconscious_description,
}
