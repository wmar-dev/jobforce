# ---------------------------------------------------------------------------
# Whatnot (whatnot.com) — company's own custom careers site (Next.js).
# Title comes through fine via the generic adapter's <h1>, but there is no
# og:site_name/footer copyright to derive company_name from, so it's fixed.
# Location is a "Location" label <p> followed by a sibling <section> holding
# one <p> per office (joined with "; "). The description lives in a div
# uniquely identified by its "max-w-[75ch]" prose-width utility class.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "whatnot.com"


def _whatnot_location(doc: BeautifulSoup, url: str) -> str | None:
    label = doc.find(lambda tag: tag.name == "p" and tag.get_text(strip=True).lower() == "location")
    if not isinstance(label, Tag):
        return None
    section = label.find_next_sibling("section")
    if not isinstance(section, Tag):
        return None
    parts = [t for p in section.find_all("p") if (t := _text(p))]
    return "; ".join(parts) if parts else None


def _whatnot_description(doc: BeautifulSoup, url: str) -> str | None:
    container = next(
        (
            div
            for div in doc.find_all("div")
            if any("max-w-[75ch]" in c for c in (div.get("class") or []))
        ),
        None,
    )
    return _to_markdown(container)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Whatnot",
    "location": _whatnot_location,
    "description": _whatnot_description,
}
