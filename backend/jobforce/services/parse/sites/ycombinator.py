# ---------------------------------------------------------------------------
# Y Combinator jobs board (ycombinator.com/companies/<slug>/jobs/<id>) — a
# multi-tenant board like Ashby/Greenhouse hosting many YC companies'
# postings, so company_name must come from the posting's own h2.text-2xl
# rather than a generic og:site_name (which is just "Y Combinator"
# site-wide); location is one of several bullet-separated spans next to the
# title with no dedicated class.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "ycombinator.com"


def _ycombinator_company(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h2.text-2xl"))


def _ycombinator_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1 is None:
        return None
    meta_row = h1.find_next_sibling("div")
    if meta_row is None:
        return None
    spans = [
        s
        for s in meta_row.find_all("span", recursive=False)
        if "mx-2" not in (s.get("class") or [])
    ]
    return _text(spans[-1]) if spans else None


def _ycombinator_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("div.grow.space-y-5"))


ADAPTER: dict[str, Any] = {
    "company_name": _ycombinator_company,
    "location": _ycombinator_location,
    "description": _ycombinator_description,
}
