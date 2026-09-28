# ---------------------------------------------------------------------------
# Upstart (careers.upstart.com) — custom single-tenant careers site (block-CMS
# layout). title and description already extract fine via the generic
# adapter. company_name has no on-page element, so it's fixed. Location has
# no dedicated element either, and its markup varies by posting: sometimes a
# "Position location" <strong> label inline in a <p> (followed by either
# "in the following locations: X" or the bare value "X"), sometimes a
# "Position Location" <h2> heading followed by a sibling <p> of prose (e.g.
# "This role is available remotely...").
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "careers.upstart.com"

_LOCATION_LABEL = "position location"
_LOCATION_LIST_PREFIX = "in the following locations:"
_LABEL_PREFIX_RE = re.compile(r"(?i)^position location\s*[-:–—]*\s*")


def _upstart_location(doc: BeautifulSoup, url: str) -> str | None:
    # The label's trailing punctuation varies ("Position location", "Position
    # Location -", "Position Location:"), so match on prefix rather than
    # exact text.
    label = doc.find(
        lambda tag: (
            tag.name in ("strong", "h1", "h2", "h3", "h4")
            and (tag.get_text(strip=True) or "").lower().startswith(_LOCATION_LABEL)
        )
    )
    if not label:
        return None

    if label.name == "strong":
        text = _text(label.find_parent("p")) or ""
        idx = text.lower().find(_LOCATION_LIST_PREFIX)
        if idx != -1:
            return text[idx + len(_LOCATION_LIST_PREFIX) :].strip() or None
        return _LABEL_PREFIX_RE.sub("", text).strip() or None

    sibling_text = _text(label.find_next_sibling()) or ""
    if "remote" in sibling_text.lower():
        return "Remote"
    return sibling_text.strip() or None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Upstart",
    "location": _upstart_location,
}
