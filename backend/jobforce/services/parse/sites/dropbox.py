# ---------------------------------------------------------------------------
# Dropbox (dropbox.jobs/en/jobs/<id>/<slug>) — company_name and location come
# from the page's own "#js-job-posting" schema.org JobPosting JSON-LD block,
# since the generic adapter's og:site_name only yields the generic "Dropbox
# Careers" and there's no plain-text location element.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup
from markdownify import markdownify as md

HOSTNAME = "dropbox.jobs"


def _dropbox_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    import json as _json

    script = doc.select_one("#js-job-posting")
    if script is None:
        return {}
    try:
        d = _json.loads(script.string or "")
    except Exception:
        return {}
    return d if isinstance(d, dict) else {}


def _dropbox_company(doc: BeautifulSoup, url: str) -> str | None:
    d = _dropbox_jsonld(doc)
    return (d.get("hiringOrganization") or {}).get("name") or None


def _dropbox_location(doc: BeautifulSoup, url: str) -> str | None:
    d = _dropbox_jsonld(doc)
    return (d.get("jobLocation") or {}).get("name") or None


def _dropbox_description(doc: BeautifulSoup, url: str) -> str | None:
    # The generic adapter finds no plain-text description container on this
    # React-rendered page; the JSON-LD "description" field is itself an HTML
    # string, so convert it directly rather than via a BeautifulSoup Tag.
    d = _dropbox_jsonld(doc)
    html = d.get("description")
    if not html:
        return None
    result = md(html, heading_style="ATX", bullets="-", strip=["a", "img"]).strip()
    return result or None


ADAPTER: dict[str, Any] = {
    "company_name": _dropbox_company,
    "location": _dropbox_location,
    "description": _dropbox_description,
}
