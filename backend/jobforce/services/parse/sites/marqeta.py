# ---------------------------------------------------------------------------
# Marqeta (marqeta.com) — custom Next.js careers page (single-tenant; the
# "Apply now" button posts to jobs.ashbyhq.com but the listing page itself is
# marqeta.com). No og:site_name meta and no distinguishing classes on the
# location field: the sidebar lists department / workplace type / employment
# type / location as four sibling divs all sharing the exact same
# "hidden md:block" class, so the location div is identified structurally by
# its nested sub-label <span> child. Job body content lives in one
# ".careers-content" container.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "marqeta.com"


def _marqeta_location(doc: BeautifulSoup, url: str) -> str | None:
    for div in doc.find_all("div", class_=["hidden", "md:block"]):
        if div.get("class") != ["hidden", "md:block"]:
            continue
        if div.find("span") is None:
            continue
        label = div.find(string=True, recursive=False)
        if label and (text := label.strip()):
            return text
    return None


def _marqeta_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".careers-content"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Marqeta",
    "location": _marqeta_location,
    "description": _marqeta_description,
}
