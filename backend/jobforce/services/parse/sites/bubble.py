# ---------------------------------------------------------------------------
# Bubble (bubble.io) — dogfooded on their own no-code builder, so job pages
# have no stable CSS hooks (hashed per-build class names); location and
# description are pulled from the page's own text structure instead.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "bubble.io"


def _bubble_location(doc: BeautifulSoup, url: str) -> str | None:
    label = next(
        (s for s in doc.find_all("strong") if "location" in s.get_text(strip=True).lower()),
        None,
    )
    if label is None:
        return None
    container = label.find_parent("p")
    if container is None:
        return None
    # The "Location:" <strong> label shows up in three different layouts
    # across job pages: alone in its own <p> (sentence follows in the next
    # <p>), followed by the sentence in the same <p>, or trailing an
    # unrelated (e.g. compensation) sentence in the same <p> with the
    # location sentence in the next <p>. Reading only what follows the
    # label *within its own paragraph* handles all three: it's empty in the
    # first and third cases (falls through to the next <p>) and is the
    # sentence itself in the second.
    parts = [
        sib.get_text(separator=" ") if isinstance(sib, Tag) else str(sib)
        for sib in label.next_siblings
    ]
    remainder = "".join(parts).strip()
    if remainder:
        return remainder
    sibling = container.find_next_sibling("p")
    return _text(sibling)


def _bubble_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("div.main-page"))


ADAPTER: dict[str, Any] = {
    "location": _bubble_location,
    "description": _bubble_description,
}
