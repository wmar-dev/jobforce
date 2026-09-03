# ---------------------------------------------------------------------------
# Meta careers (metacareers.com) — a React/Relay SPA whose h1 title, class
# names, and DOM structure are unstable StyleX-generated atomic classes
# (e.g. "x1motxo8 x1dg8jwx ..."), and which exposes no plain-text company or
# location element and no og:site_name meta tag. This is not a hydration
# race — scout_fetch's captured HTML already contains the fully-populated
# job data by the time the bare "h1, main h2" wait resolves — the generic
# adapter simply has no selector for it. All real job data lives in a
# schema.org JobPosting JSON-LD <script> block (same pattern as the
# Dropbox/Workable adapters). Unlike those, Meta splits the body into
# separate "description" / "responsibilities" / "qualifications" string
# fields (the latter two using literal "&nbsp;" as a bullet separator
# instead of markup), and jobLocation is always a list — Meta postings
# routinely list several hub cities for the same role.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

HOSTNAME = "metacareers.com"


def _meta_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    import json as _json

    for s in doc.find_all("script", type="application/ld+json"):
        try:
            d = _json.loads(s.string or "")
        except Exception:
            continue
        if d.get("@type") == "JobPosting":
            return d  # type: ignore[no-any-return]
    return {}


def _meta_company(doc: BeautifulSoup, url: str) -> str | None:
    d = _meta_jsonld(doc)
    return (d.get("hiringOrganization") or {}).get("name") or None


def _meta_location(doc: BeautifulSoup, url: str) -> str | None:
    d = _meta_jsonld(doc)
    job_location = d.get("jobLocation") or []
    if isinstance(job_location, dict):
        job_location = [job_location]
    names = []
    for place in job_location:
        name = place.get("name")
        if not name:
            addr = place.get("address") or {}
            city = addr.get("addressLocality", "")
            region = addr.get("addressRegion", "")
            name = f"{city}, {region}" if city and region else city or region or None
        if name:
            names.append(name)
    return "; ".join(names) if names else None


def _meta_bullets(raw: str) -> list[str]:
    # responsibilities/qualifications use literal "&nbsp;" as a bullet
    # separator rather than markup or a delimiter list.
    return [item.strip() for item in raw.split("&nbsp;") if item.strip()]


def _meta_description(doc: BeautifulSoup, url: str) -> str | None:
    d = _meta_jsonld(doc)
    parts: list[str] = []
    if summary := d.get("description"):
        parts.append(summary.strip())
    if responsibilities := d.get("responsibilities"):
        bullets = "\n".join(f"- {item}" for item in _meta_bullets(responsibilities))
        parts.append(f"**Responsibilities:**\n{bullets}")
    if qualifications := d.get("qualifications"):
        bullets = "\n".join(f"- {item}" for item in _meta_bullets(qualifications))
        parts.append(f"**Minimum Qualifications:**\n{bullets}")
    return "\n\n".join(parts) if parts else None


def _meta_role_type(doc: BeautifulSoup, url: str) -> str | None:
    d = _meta_jsonld(doc)
    emp = (d.get("employmentType") or "").strip().lower()
    return {
        "full-time": "full-time",
        "part-time": "part-time",
        "contract": "contract",
        "internship": "internship",
        "intern": "internship",
    }.get(emp)


ADAPTER: dict[str, Any] = {
    "company_name": _meta_company,
    "location": _meta_location,
    "description": _meta_description,
    "role_type": _meta_role_type,
}
