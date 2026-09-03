# ---------------------------------------------------------------------------
# Latent Labs (latentlabs.com) — WordPress job template. Location sits in a
# `.tag_list span.tag` inside the `.banner_title` header (not the generic
# `.location` class). The body is a series of `.box_width > .right_desc`
# sections (opportunity, requirements, apply, ...) with no "description" hook.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "latentlabs.com"


def _latentlabs_location(doc: BeautifulSoup, url: str) -> str | None:
    banner = doc.select_one(".banner_title")
    if not banner:
        return None
    tag = banner.select_one(".tag_list .tag")
    return _text(tag)


def _latentlabs_description(doc: BeautifulSoup, url: str) -> str | None:
    parts = [
        md
        for el in doc.select(".job_details_section .box_width .right_desc")
        if (md := _to_markdown(el))
    ]
    return "\n\n".join(parts) if parts else None


ADAPTER: dict[str, Any] = {
    "location": _latentlabs_location,
    "description": _latentlabs_description,
}
