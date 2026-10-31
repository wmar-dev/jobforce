# ---------------------------------------------------------------------------
# AMD careers (careers.amd.com) — Jibe-hosted Angular board. `og:site_name`
# is the whole "<title> in <city> | Advanced Micro Devices, Inc" page title,
# so the generic company fallback is junk; there's no `.location` element;
# and `job-description-container` holds untranslated i18n keys
# ("JOB_DESCRIPTION.SHARE.HTML"). The ld+json JobPosting block carries the
# real location and the full description (role + boilerplate), so both are
# pulled from there. Company is fixed to "AMD" to match config.yaml.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown, find_jobposting_jsonld

HOSTNAME = "careers.amd.com"


def _amd_location(doc: BeautifulSoup, url: str) -> str | None:
    data = find_jobposting_jsonld(doc) or {}
    job_location = data.get("jobLocation") or {}
    if isinstance(job_location, list):
        job_location = job_location[0] if job_location else {}
    addr = job_location.get("address") or {}
    parts = [addr.get("addressLocality"), addr.get("addressRegion")]
    # Empty fields are filled with the literal placeholder "UNAVAILABLE"
    return ", ".join(p for p in parts if p and p != "UNAVAILABLE") or None


def _amd_description(doc: BeautifulSoup, url: str) -> str | None:
    raw = (find_jobposting_jsonld(doc) or {}).get("description") or ""
    if not raw:
        return None
    return _to_markdown(BeautifulSoup(raw, "lxml"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "AMD",
    "location": _amd_location,
    "description": _amd_description,
}
