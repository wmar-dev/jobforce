# ---------------------------------------------------------------------------
# Stripe site adapter — stripe.com/jobs/listing/<slug>/<id>
# Page structure: persistent header has its own <h1>, so a bare "h1" selector
# grabs "Stripe logo Jobs" instead of the job title. Job title is the first
# h1.Copy__title inside .Copy__header. Office locations/Team/Job type are
# label/value pairs under .JobDetailCardProperty__title. Description body is
# the .ArticleMarkdown container.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "stripe.com"


def _stripe_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".Copy__header h1"))


def _stripe_location(doc: BeautifulSoup, url: str) -> str | None:
    for label in doc.select(".JobDetailCardProperty__title"):
        if (label.get_text(strip=True) or "").lower() == "office locations":
            sib = label.find_next_sibling()
            if sib and (t := _text(sib)):
                return t
    return None


def _stripe_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".ArticleMarkdown")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Stripe",
    "title": _stripe_title,
    "location": _stripe_location,
    "description": _stripe_description,
}
