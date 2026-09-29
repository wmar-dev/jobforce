# ---------------------------------------------------------------------------
# Stripe site adapter — stripe.com/jobs/listing/<slug>/<id> (old layout) and
# stripe.com/careers/listing/<slug>/<id> (redesigned "hds-" layout).
#
# Old layout: persistent header has its own <h1>, so a bare "h1" selector
# grabs "Stripe logo Jobs" instead of the job title. Job title is the first
# h1.Copy__title inside .Copy__header. Office locations/Team/Job type are
# label/value pairs under .JobDetailCardProperty__title. Description body is
# the .ArticleMarkdown container.
#
# New layout: title is h1.careers-detail-hero__title (also works via the
# generic adapter's bare <h1> fallback, since there's no second header <h1>
# on this layout). Office locations/Team/Employment type are dt/dd pairs
# under .careers-listing-details__fact. Description body is the
# .careers-listing-details__body container.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "stripe.com"


def _stripe_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".Copy__header h1")) or _text(
        doc.select_one(".careers-detail-hero__title")
    )


def _stripe_location(doc: BeautifulSoup, url: str) -> str | None:
    for fact in doc.select(".careers-listing-details__fact"):
        dt = fact.find("dt")
        label = (dt.get_text(strip=True) or "").lower() if dt else ""
        if label.startswith("office location"):
            dd = fact.find("dd")
            if dd and (t := _text(dd)):
                return t
    for fact in doc.select(".careers-listing-details__fact"):
        dt = fact.find("dt")
        label = (dt.get_text(strip=True) or "").lower() if dt else ""
        if label.startswith("remote location"):
            dd = fact.find("dd")
            if dd and (t := _text(dd)):
                return t
    for old_label in doc.select(".JobDetailCardProperty__title"):
        if (old_label.get_text(strip=True) or "").lower() == "office locations":
            sib = old_label.find_next_sibling()
            if sib and (t := _text(sib)):
                return t
    return None


def _stripe_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".careers-listing-details__body") or doc.select_one(".ArticleMarkdown")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Stripe",
    "title": _stripe_title,
    "location": _stripe_location,
    "description": _stripe_description,
}
