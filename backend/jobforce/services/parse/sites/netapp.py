# ---------------------------------------------------------------------------
# NetApp (careers.netapp.com) — a Radancy Talentbrew-templated career site.
# The page has two <h1> elements: a generic marketing hero tagline that
# appears first in the DOM ("Explore roles where you can make measurable
# impact..."), and the real job title further down in
# `h1.ajd_header__job-title` — the generic adapter's bare "h1" selector
# grabs the hero tagline instead. There's also no `og:site_name` (or any
# company element) on this ATS template, so company_name comes back null;
# this domain only ever serves NetApp postings, so it's a fixed value.
# location and description already extract correctly via the generic
# adapter's class selectors (a `.job-location` span and a `.job-description`
# container both carry the real content), so neither is overridden here.
# Note: role_type comes back as a false-positive "contract" via the generic
# adapter's whole-body `\bcontract\b` scan, tripped by unrelated footer
# boilerplate ("...regarding contract compliance..."). That can't be fixed
# from a site adapter alone — `merge()` only applies an override when it's
# truthy, so returning None here wouldn't blank out the wrong base value,
# it would just fall through to it. Leaving as a known generic-adapter gap.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "careers.netapp.com"


def _netapp_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h1.ajd_header__job-title"))


ADAPTER: dict[str, Any] = {
    "title": _netapp_title,
    "company_name": lambda doc, url: "NetApp",
}
