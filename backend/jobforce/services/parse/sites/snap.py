# ---------------------------------------------------------------------------
# Snap Inc (careers.snap.com) — company's own custom careers site built on a
# design-system component library (all class names are hashed "css-xxxxxxx"
# utility classes, no semantic hooks). Title comes through fine via the
# generic adapter's <h1>, but there is no og:site_name/footer copyright to
# derive company_name from, so it's fixed. Locations are a list of sibling
# <p> tags inside the <section> that also contains a globe icon (distinct
# from sibling sections holding "Full time"/"Posted x days ago"/req id, which
# share the same class). The page renders two elements sharing the same
# data-testid ("sdsm-content-body-content") — one is the small
# location/date/id metadata block, the other (much larger) is the actual job
# description — so description picks the longer of the two.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "careers.snap.com"


def _snap_location(doc: BeautifulSoup, url: str) -> str | None:
    globe = doc.select_one(".sds-icon-globe")
    if not globe:
        return None
    section = globe.find_parent("section")
    if not section:
        return None
    parts = [t for p in section.select("p") if (t := _text(p))]
    return "; ".join(parts) if parts else None


def _snap_description(doc: BeautifulSoup, url: str) -> str | None:
    candidates = [
        c for c in doc.select('[data-testid="sdsm-content-body-content"]') if isinstance(c, Tag)
    ]
    if not candidates:
        return None
    longest = max(candidates, key=lambda c: len(c.get_text()))
    return _to_markdown(longest)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Snap Inc.",
    "location": _snap_location,
    "description": _snap_description,
}
