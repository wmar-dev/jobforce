# ---------------------------------------------------------------------------
# Accenture (accenture.com) — single-tenant AEM careers site. No on-page
# company element (single employer, so it's a fixed lambda). Location lives
# in a "Locations" accordion panel as one <p> per city; joined for
# multi-location roles. Description lives in the "Job Description" accordion
# panel, matched by id suffix since the accordion's id prefix is a per-page
# random hash.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "accenture.com"


def _accenture_locations_panel(doc: BeautifulSoup) -> Tag | None:
    for heading in doc.select(".rad-accordion-atom__toggle-title"):
        if _text(heading) == "Locations":
            accordion = heading.find_parent("div", class_="rad-accordion-atom")
            if accordion:
                return accordion.select_one(".rad-accordion-atom__content")
    return None


def _accenture_location(doc: BeautifulSoup, url: str) -> str | None:
    panel = _accenture_locations_panel(doc)
    if panel:
        cities = [t for p in panel.select("p") if (t := _text(p))]
        if cities:
            return "; ".join(cities)
    wrapper = doc.select_one("[data-joblocation]")
    if wrapper:
        return (wrapper.get("data-joblocation") or "").strip() or None  # type: ignore[union-attr]
    return None


def _accenture_description(doc: BeautifulSoup, url: str) -> str | None:
    for heading in doc.select(".rad-accordion-atom__toggle-title"):
        if _text(heading) == "Job Description":
            accordion = heading.find_parent("div", class_="rad-accordion-atom")
            if accordion:
                content = accordion.select_one(".rad-accordion-atom__content")
                return _to_markdown(content)
    return None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Accenture",
    "location": _accenture_location,
    "description": _accenture_description,
}
