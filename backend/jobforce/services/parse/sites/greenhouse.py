# ---------------------------------------------------------------------------
# Greenhouse site adapter — boards.greenhouse.io / job-boards.greenhouse.io
# URL: boards.greenhouse.io/<company>/jobs/<id>
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAMES = ["boards.greenhouse.io", "job-boards.greenhouse.io"]


def _greenhouse_company(doc: BeautifulSoup, url: str) -> str | None:
    # boards.greenhouse.io/<company>/jobs/<id> — extract from path
    parts = urlparse(url).path.strip("/").split("/")
    if len(parts) >= 1 and parts[0] not in ("jobs",):
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _greenhouse_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job__location")
    return _text(el)


ADAPTER: dict[str, Any] = {
    "company_name": _greenhouse_company,
    "location": _greenhouse_location,
}
