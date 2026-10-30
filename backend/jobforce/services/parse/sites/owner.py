# ---------------------------------------------------------------------------
# Owner (owner.com) — Webflow careers page at /careers/role?=<uuid>. Job
# fields are rendered client-side into elements tagged with data-role-*
# attributes: data-role-title (h1), data-role-location (p), and the body
# split across data-role-opening / data-role-html / data-role-additional
# rich-text divs (usually only "opening" is populated). Title is picked up
# by the generic adapter; company name never appears in og:site_name.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "owner.com"

_BODY_ATTRS = ("data-role-opening", "data-role-html", "data-role-additional")


def _owner_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("[data-role-location]"))


def _owner_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [
        md
        for attr in _BODY_ATTRS
        if (el := doc.select_one(f"[{attr}]")) and (md := _to_markdown(el))
    ]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Owner",
    "location": _owner_location,
    "description": _owner_description,
}
