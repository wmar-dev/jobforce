# ---------------------------------------------------------------------------
# Dayforce (*.dayforcehcm.com) — a pure client-rendered SPA (curl returns an
# essentially empty shell); the `data-testid` attributes on job-detail
# elements are only present briefly right after hydration and reliably
# disappear on a later read of the same loaded page — too flaky to select
# on — but `<meta name="description">` carries the full job body as
# HTML-escaped markup and is present immediately, so use that for
# description instead of any DOM element. There's no per-tenant company
# name element anywhere in the DOM (the only branding is the platform's own
# "Dayforce HCM, Inc." copyright, which isn't the actual employer for other
# tenants), so company_name is inferred from the URL's tenant path segment
# instead (e.g. .../mydayforce/alljobs/jobs/... -> "Mydayforce").
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import normalize_description

HOSTNAME = "dayforcehcm.com"

_LOCALE_RE = re.compile(r"[a-z]{2}-[A-Z]{2}")


def _dayforce_company(doc: BeautifulSoup, url: str) -> str | None:
    segments = [s for s in urlparse(url).path.split("/") if s]
    tenant = next((s for s in segments if not _LOCALE_RE.fullmatch(s)), None)
    if tenant is None:
        return None
    return " ".join(w.capitalize() for w in tenant.replace("-", " ").split()) or None


def _dayforce_description(doc: BeautifulSoup, url: str) -> str | None:
    meta = doc.find("meta", attrs={"name": "description"})
    if meta is None:
        return None
    return normalize_description(meta.get("content"))  # type: ignore[arg-type]


ADAPTER: dict[str, Any] = {
    "company_name": _dayforce_company,
    "description": _dayforce_description,
}
