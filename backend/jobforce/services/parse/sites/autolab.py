# ---------------------------------------------------------------------------
# Autolab (autolab.ai) — single-page careers site. Every role is a
# <details class="role" id="slug"> block; the URL fragment (#slug) picks the
# role. Without a matching fragment nothing is extracted.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "autolab.ai"


def _role(doc: BeautifulSoup, url: str) -> Tag | None:
    fragment = urlparse(url).fragment
    if not fragment:
        return None
    for el in doc.select("details.role"):
        if el.get("id") == fragment:
            return el
    return None


def _autolab_title(doc: BeautifulSoup, url: str) -> str | None:
    role = _role(doc, url)
    return _text(role.select_one("h3")) if role else None


def _autolab_location(doc: BeautifulSoup, url: str) -> str | None:
    role = _role(doc, url)
    meta = _text(role.select_one(".rmeta")) if role else None
    if not meta:
        return None
    # "San Francisco, California · Remote (US) · Full-time" -> drop the job type
    parts = [p.strip() for p in meta.split("·")]
    return " · ".join(p for p in parts if p and p.lower() != "full-time") or None


def _autolab_description(doc: BeautifulSoup, url: str) -> str | None:
    role = _role(doc, url)
    return _to_markdown(role.select_one(".rbody")) if role else None


ADAPTER: dict[str, Any] = {
    "title": _autolab_title,
    "company_name": lambda doc, url: "Autolab",
    "location": _autolab_location,
    "description": _autolab_description,
}
