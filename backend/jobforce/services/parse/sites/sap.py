# ---------------------------------------------------------------------------
# SAP (jobs.sap.com) — SuccessFactors/jobs2web careers template. title and
# description already extract fine via the generic adapter. company_name has
# no data-company/.company-name element or og:site_name meta, but the page
# marks up a schema.org JobPosting via microdata (not JSON-LD), including a
# <meta itemprop="hiringOrganization"> — read that directly. location is
# actively wrong under the generic adapter: its ".job-location" selector
# matches a "Nearest Major Market" trailer paragraph baked into the
# description body rather than the real location, so pull the dedicated
# ".jobGeoLocation" span instead.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "jobs.sap.com"


def _sap_company(doc: BeautifulSoup, url: str) -> str | None:
    meta = doc.select_one('meta[itemprop="hiringOrganization"]')
    if not meta:
        return None
    return (meta.get("content") or "").strip() or None  # type: ignore[union-attr]


def _sap_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".jobGeoLocation"))


ADAPTER: dict[str, Any] = {
    "company_name": _sap_company,
    "location": _sap_location,
}
