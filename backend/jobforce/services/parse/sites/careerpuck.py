# ---------------------------------------------------------------------------
# CareerPuck (app.careerpuck.com) — multi-tenant Greenhouse front-end. Company
# name is the logo <img alt="<Company> logo">; location is the styled-component
# div whose class starts with "JobPagePublic__Location".
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "app.careerpuck.com"


def _careerpuck_company(doc: BeautifulSoup, url: str) -> str | None:
    img = doc.select_one("[class*=JobPagePublic__LogoContainer] img[alt]")
    if not img:
        return None
    alt = str(img.get("alt") or "").strip()
    alt = alt.removesuffix(" logo").strip()
    return alt or None


def _careerpuck_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("[class*=JobPagePublic__Location]"))


ADAPTER: dict[str, Any] = {
    "company_name": _careerpuck_company,
    "location": _careerpuck_location,
}
