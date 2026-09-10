# ---------------------------------------------------------------------------
# Factory (factory.com) — Next.js site. Location/type/tags live as label/value
# <p> pairs inside <article>; the full rich-text description is a separate
# <div> further down the page (the page's <meta name="description"> and
# JobPosting JSON-LD are both truncated with an ellipsis, so neither is usable
# as the description source). That div has no stable class of its own (only a
# long list of Tailwind arbitrary-variant utilities), but every posting opens
# with the same boilerplate "About Factory" heading (id="about-factory") as
# its first child, so anchor on that heading's parent instead. The div
# immediately after </article> is a mobile-only "Table of Contents" widget,
# not the description — do not use find_next_sibling on <article> here.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "factory.com"


def _factory_label_value(doc: BeautifulSoup, label: str) -> str | None:
    article = doc.find("article")
    if article is None:
        return None
    label_p = article.find("p", string=label)
    if label_p is None:
        return None
    return _text(label_p.find_next_sibling("p"))


def _factory_location(doc: BeautifulSoup, url: str) -> str | None:
    return _factory_label_value(doc, "LOCATION")


def _factory_description(doc: BeautifulSoup, url: str) -> str | None:
    heading = doc.find(id="about-factory")
    if heading is None:
        return None
    container = heading.find_parent("div")
    return _to_markdown(container)


ADAPTER: dict[str, Any] = {
    "location": _factory_location,
    "description": _factory_description,
}
