# ---------------------------------------------------------------------------
# Greenhouse site adapter — boards.greenhouse.io / job-boards.greenhouse.io
# (plus the EU-region job-boards.eu.greenhouse.io tenants, e.g. Groww)
# URL: boards.greenhouse.io/<company>/jobs/<id>
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from .._common import _text, normalize_posted_at

HOSTNAMES = ["boards.greenhouse.io", "job-boards.greenhouse.io", "job-boards.eu.greenhouse.io"]


def _greenhouse_company(doc: BeautifulSoup, url: str) -> str | None:
    # boards.greenhouse.io/<company>/jobs/<id> — extract from path
    parsed = urlparse(url)
    parts = parsed.path.strip("/").split("/")
    if parts[0] == "embed":
        # boards.greenhouse.io/embed/job_app?for=<board>&token=<id>
        board = (parse_qs(parsed.query).get("for") or [""])[0].rstrip("0123456789")
        return " ".join(w.capitalize() for w in board.replace("-", " ").split()) or None
    if len(parts) >= 1 and parts[0] not in ("jobs",):
        return " ".join(w.capitalize() for w in parts[0].replace("-", " ").split())
    return None


def _greenhouse_location(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one(".job__location")
    return _text(el)


_PUBLISHED_AT_RE = re.compile(r'"published_at"\s*:\s*"([^"]+)"')


def _greenhouse_posted_at(doc: BeautifulSoup, url: str) -> str | None:
    # job-boards.greenhouse.io is a Remix app: the job payload (including
    # `published_at`, the original posting date) is embedded in an inline
    # script, but there is no visible date or JSON-LD on the page.
    for script in doc.find_all("script"):
        match = _PUBLISHED_AT_RE.search(script.string or "")
        if match and (normalized := normalize_posted_at(match.group(1))):
            return normalized
    return None


ADAPTER: dict[str, Any] = {
    "company_name": _greenhouse_company,
    "location": _greenhouse_location,
    "posted_at": _greenhouse_posted_at,
}
