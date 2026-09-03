# ---------------------------------------------------------------------------
# Breezy HR (<company>.breezy.hr/p/<id>-<slug>) — shared ATS matched by
# hostname suffix. The page has two <h1>s (the site brand/logo, then the
# real job title), so the generic adapter's bare "h1" selector grabs the
# wrong one. Company name comes from the subdomain, mirroring the Workday
# adapter's approach.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "breezy.hr"


def _breezy_company(doc: BeautifulSoup, url: str) -> str | None:
    hostname = urlparse(url).hostname or ""
    subdomain = hostname.split(".")[0]
    if subdomain and subdomain not in ("www",):
        return " ".join(w.capitalize() for w in subdomain.replace("-", " ").split())
    return None


def _breezy_title(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".banner h1"))


ADAPTER: dict[str, Any] = {
    "company_name": _breezy_company,
    "title": _breezy_title,
}
