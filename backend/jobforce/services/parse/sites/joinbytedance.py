# ---------------------------------------------------------------------------
# ByteDance (joinbytedance.com) — company's own custom careers site (not a
# shared ATS). The job title lives in an <h2>, not an <h1>, so the generic
# adapter falls through to the <title> tag and its "strip everything after
# a hyphen" heuristic mangles titles like "...Engineer- Metadata Storage"
# down to "...Engineer". There is also no og:site_name/footer copyright to
# derive company_name from, so it's fixed. Location is rendered as a label/
# value pair of sibling <p> tags ("Location:" / "San Jose"), and the job body
# lives in a single flex-col container of heading/body <p> pairs
# ("Responsibilities", "Qualifications", etc.).
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "joinbytedance.com"


def _find_label_value(doc: BeautifulSoup, label: str) -> str | None:
    for p in doc.find_all("p"):
        if p.get_text(strip=True) == label:
            sibling = p.find_next_sibling("p")
            return _text(sibling)
    return None


def _joinbytedance_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h2"))


def _joinbytedance_location(doc: BeautifulSoup, url: str) -> str | None:
    return _find_label_value(doc, "Location:")


def _joinbytedance_description(doc: BeautifulSoup, url: str) -> str | None:
    heading = doc.find(
        lambda tag: tag.name == "p" and tag.get_text(strip=True) == "Responsibilities"
    )
    if not isinstance(heading, Tag):
        return None
    container = heading.find_parent("div")
    return _to_markdown(container)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "ByteDance",
    "title": _joinbytedance_title,
    "location": _joinbytedance_location,
    "description": _joinbytedance_description,
}
