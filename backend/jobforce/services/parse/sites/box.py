# ---------------------------------------------------------------------------
# Box careers (careers.box.com) — not a hydration race: scout_fetch's
# captured HTML already has the job data fully rendered. The generic
# adapter's `.location` / `[class*="description"]` selectors simply don't
# match this page's markup — location lives in a plain `<a>` inside a
# `<ul class="job-meta">` list item (no "location" class anywhere), and the
# description sits in an `<article class="cms-content">` (no "description"
# in its class name either). title/company_name already resolve fine via
# the generic adapter's `h1` / `og:site_name` fallbacks. Rather than hand-
# roll selectors for the DOM, both broken fields are pulled from the
# `<script type="application/ld+json">` JobPosting block every listing page
# embeds (same pattern as the Meta/Wayve adapters) — it mirrors the DOM
# content exactly and is far less brittle. `employmentType` is always the
# literal string "OTHER" on this board, so role_type is left unoverridden
# (the generic full-time/part-time/contract/internship text scan is the
# best available signal, and Box listings don't state it in the body text).
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "careers.box.com"


def _box_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    for s in doc.find_all("script", type="application/ld+json"):
        try:
            d = json.loads(s.string or "")
        except Exception:
            continue
        if d.get("@type") == "JobPosting":
            return d  # type: ignore[no-any-return]
    return {}


def _box_location(doc: BeautifulSoup, url: str) -> str | None:
    job_location = _box_jsonld(doc).get("jobLocation") or {}
    name = job_location.get("name")
    if name:
        return str(name).strip() or None
    addr = job_location.get("address") or {}
    city = addr.get("addressLocality", "")
    region = addr.get("addressRegion", "")
    if city and region:
        return f"{city}, {region}"
    return city or region or None


def _box_description(doc: BeautifulSoup, url: str) -> str | None:
    raw = _box_jsonld(doc).get("description") or ""
    if not raw:
        return None
    return _to_markdown(BeautifulSoup(raw, "lxml"))


ADAPTER: dict[str, Any] = {
    "location": _box_location,
    "description": _box_description,
}
