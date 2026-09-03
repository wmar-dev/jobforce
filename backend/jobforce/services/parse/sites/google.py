# ---------------------------------------------------------------------------
# Google Careers site adapter — google.com/about/careers/applications/jobs/results/<slug>
# Angular SPA: the sitewide <h1> is a generic "job details" label, and a
# "Jobs search results" <h2> in the sidebar list precedes the real job <h2>
# in some layouts, so generic selectors miss the actual title/company.
# Location renders as a Material Icon ligature ("place") followed by a
# sibling <span> with the value, not plain text a CSS class can target.
# The job's own content lives in a <div data-id="..."> ancestor of the
# title <h2>; description rows sit between the "Apply" row and the trailing
# EEO/privacy boilerplate row.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "google.com"


def _google_careers_container(doc: BeautifulSoup) -> Tag | None:
    h2 = doc.select_one("main h2")
    if h2 is None:
        return None
    node = h2.parent
    while node is not None:
        if node.has_attr("data-id"):
            return node
        node = node.parent
    return None


def _google_careers_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("main h2"))


def _google_careers_location(doc: BeautifulSoup, url: str) -> str | None:
    main = doc.find("main")
    if main is None:
        return None
    icon = next((i for i in main.find_all("i") if (i.get_text() or "").strip() == "place"), None)
    if icon is None:
        return None
    return _text(icon.find_next_sibling("span"))


def _google_careers_description(doc: BeautifulSoup, url: str) -> str | None:
    container = _google_careers_container(doc)
    if container is None:
        return None
    started = False
    parts = []
    for child in container.find_all("div", recursive=False):
        text = child.get_text(" ", strip=True)
        if not text:
            continue
        if not started:
            if "Apply" in text:
                started = True
            continue
        if "Privacy Policy" in text or "equal opportunity" in text.lower():
            break
        if md_part := _to_markdown(child):
            parts.append(md_part)
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Google",
    "title": _google_careers_title,
    "location": _google_careers_location,
    "description": _google_careers_description,
}
