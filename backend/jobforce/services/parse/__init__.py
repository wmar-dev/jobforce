"""Deterministic job page parser — mirrors chrome-extension/content.js adapter architecture."""

from __future__ import annotations

import logging
from typing import Any
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from ._common import GENERIC_ADAPTER, slug_to_location
from ._hn import _parse_hn
from .sites import SITE_ADAPTERS

logger = logging.getLogger(__name__)

__all__ = [
    "GENERIC_ADAPTER",
    "SITE_ADAPTERS",
    "_match_adapter",
    "merge",
    "parse_html",
    "run_adapter",
    "slug_to_location",
]

# ---------------------------------------------------------------------------
# Framework
# ---------------------------------------------------------------------------


def run_adapter(adapter: dict[str, Any], doc: BeautifulSoup, url: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, fn in adapter.items():
        try:
            result[key] = fn(doc, url)
        except Exception:
            logger.warning("[parse] adapter field %r error", key, exc_info=True)
            result[key] = None
    return result


def merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for k, v in override.items():
        if v is not None and v != "":
            out[k] = v
    return out


def _match_adapter(hostname: str) -> dict[str, Any]:
    if hostname in SITE_ADAPTERS:
        return SITE_ADAPTERS[hostname]
    # suffix match for subdomain-based ATSes (e.g. acme.wd1.myworkdayjobs.com)
    for key, adapter in SITE_ADAPTERS.items():
        if hostname.endswith("." + key):
            return adapter
    return {}


def parse_html(html: str, url: str) -> dict[str, Any]:
    hostname = (urlparse(url).hostname or "").removeprefix("www.")
    if hostname == "news.ycombinator.com":
        return _parse_hn(html, url)
    doc = BeautifulSoup(html, "lxml")
    adapter = _match_adapter(hostname)
    base = run_adapter(GENERIC_ADAPTER, doc, url)
    override = run_adapter(adapter, doc, url) if adapter else {}
    return {"source_url": url, **merge(base, override)}
