# ---------------------------------------------------------------------------
# Intuitive Surgical (careers.intuitive.com/en/jobs/<id>/<req>/<slug>/) —
# title extracts fine via the generic adapter's <h1> selector, but
# company_name comes back as the og:site_name meta ("Intuitive Surgical
# Careers" instead of "Intuitive Surgical"), and location/description
# aren't exposed via any plain element the generic adapter checks.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careers.intuitive.com"


def _intuitivesurgical_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job-meta")
    if el is None:
        return None
    first_item = el.select_one("li")
    return _text(first_item)


def _intuitivesurgical_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("article.cms-content"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Intuitive Surgical",
    "location": _intuitivesurgical_location,
    "description": _intuitivesurgical_description,
}
