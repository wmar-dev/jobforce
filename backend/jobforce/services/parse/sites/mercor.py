# ---------------------------------------------------------------------------
# Mercor (mercor.com) — Next.js page with an empty rendered body. Every job
# (Ashby-sourced) is in the __NEXT_DATA__ JSON blob's `pageProps.jobs` list;
# the one for this page is the entry whose `id` is the last URL path segment.
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup
from markdownify import markdownify as md

HOSTNAME = "mercor.com"

_ROLE_TYPES = {
    "FullTime": "full-time",
    "PartTime": "part-time",
    "Contract": "contract",
    "Intern": "internship",
}


def _mercor_job(doc: BeautifulSoup, url: str) -> dict[str, Any] | None:
    script = doc.find("script", id="__NEXT_DATA__")
    if not script or not script.string:
        return None
    try:
        data = json.loads(script.string)
    except ValueError:
        return None
    jobs = data.get("props", {}).get("pageProps", {}).get("jobs")
    if not isinstance(jobs, list):
        return None
    job_id = urlparse(url).path.rstrip("/").split("/")[-1]
    return next((j for j in jobs if isinstance(j, dict) and j.get("id") == job_id), None)


def _mercor_location(doc: BeautifulSoup, url: str) -> str | None:
    job = _mercor_job(doc, url)
    loc = job.get("location") if job else None
    return loc.strip() or None if isinstance(loc, str) else None


def _mercor_description(doc: BeautifulSoup, url: str) -> str | None:
    job = _mercor_job(doc, url)
    html = job.get("descriptionHtml") if job else None
    if not isinstance(html, str):
        return None
    return md(html, heading_style="ATX", bullets="-", strip=["a", "img"]).strip() or None


def _mercor_role_type(doc: BeautifulSoup, url: str) -> str | None:
    job = _mercor_job(doc, url)
    emp = job.get("employmentType") if job else None
    return _ROLE_TYPES.get(emp) if isinstance(emp, str) else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Mercor",
    "location": _mercor_location,
    "description": _mercor_description,
    "role_type": _mercor_role_type,
}
