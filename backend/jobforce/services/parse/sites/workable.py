# ---------------------------------------------------------------------------
# Workable site adapter — jobs.workable.com/en/view/<id>/<slug> and
# apply.workable.com/<company-slug>/j/<id> (company-hosted "Apply" link).
# All fields live in a JSON-LD <script type="application/ld+json"> block.
# employmentType values: FULL_TIME, PART_TIME, CONTRACTOR, INTERN
# jobLocationType: TELECOMMUTE → "Remote"
# jobLocation is a single object on jobs.workable.com but a list on
# apply.workable.com — _workable_job_location() normalizes both.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAMES = ["jobs.workable.com", "apply.workable.com"]


def _workable_jsonld(doc: BeautifulSoup) -> dict[str, Any]:
    import json as _json

    for s in doc.find_all("script", type="application/ld+json"):
        try:
            d = _json.loads(s.string or "")
            if d.get("@type") == "JobPosting":
                return d  # type: ignore[no-any-return]
        except Exception:
            pass
    return {}


def _workable_title(doc: BeautifulSoup, url: str) -> str | None:
    return _workable_jsonld(doc).get("title") or None


def _workable_company(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    return (d.get("hiringOrganization") or {}).get("name") or None


def _workable_job_location(d: dict[str, Any]) -> dict[str, Any]:
    # jobLocation is a single object on jobs.workable.com but a list on
    # apply.workable.com — normalize to the first entry either way.
    job_location = d.get("jobLocation") or {}
    if isinstance(job_location, list):
        job_location = job_location[0] if job_location else {}
    return job_location


def _workable_location(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    if d.get("jobLocationType") == "TELECOMMUTE":
        addr = _workable_job_location(d).get("address") or {}
        city = addr.get("addressLocality", "")
        return f"{city} (Remote)" if city else "Remote"
    addr = _workable_job_location(d).get("address") or {}
    city = addr.get("addressLocality", "")
    region = addr.get("addressRegion", "")
    if city and region:
        return f"{city}, {region}"
    return city or region or None


def _workable_description(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    raw = d.get("description") or ""
    if not raw:
        return None
    return _to_markdown(BeautifulSoup(raw, "lxml"))


def _workable_role_type(doc: BeautifulSoup, url: str) -> str | None:
    d = _workable_jsonld(doc)
    emp = (d.get("employmentType") or "").upper()
    return {
        "FULL_TIME": "full-time",
        "PART_TIME": "part-time",
        "CONTRACTOR": "contract",
        "INTERN": "internship",
    }.get(emp)


ADAPTER: dict[str, Any] = {
    "company_name": _workable_company,
    "title": _workable_title,
    "location": _workable_location,
    "description": _workable_description,
    "role_type": _workable_role_type,
}
