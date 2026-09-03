# ---------------------------------------------------------------------------
# Surge AI (surgehq.ai) — Webflow CMS site. Most job pages are a templated
# `/careers?id=...` detail view (title in h2.js-title, body in
# .job-content-richtext.js-desc); a handful like `/swe` are bespoke landing
# pages with no CMS markup, so title/description fall back to the generic h1
# and a scoped <main> selection. No page exposes a per-job location string;
# every listing on the site is Remote, so it's fixed.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "surgehq.ai"


def _surgehq_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("h2.js-title"))


def _surgehq_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job-content-richtext.js-desc") or doc.select_one("main")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Surge AI",
    "title": _surgehq_title,
    "location": lambda doc, url: "Remote",
    "description": _surgehq_description,
}
