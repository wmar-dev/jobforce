# ---------------------------------------------------------------------------
# Work at a Startup (workatastartup.com) — YC's job board, an Inertia app.
# The rendered DOM has no semantic job markup; the job and company live in the
# JSON ``data-page`` attribute (props.job / props.company).
# ---------------------------------------------------------------------------

from __future__ import annotations

import json
from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "workatastartup.com"


def _props(doc: BeautifulSoup) -> dict[str, Any]:
    el = doc.select_one("[data-page]")
    if not el:
        return {}
    try:
        data = json.loads(str(el["data-page"]))
    except (ValueError, TypeError):
        return {}
    props = data.get("props") if isinstance(data, dict) else None
    return props if isinstance(props, dict) else {}


def _waas_company(doc: BeautifulSoup, url: str) -> str | None:
    name = (_props(doc).get("company") or {}).get("name")
    return name or None


def _waas_location(doc: BeautifulSoup, url: str) -> str | None:
    location = (_props(doc).get("job") or {}).get("location")
    return location or None


def _waas_description(doc: BeautifulSoup, url: str) -> str | None:
    html = (_props(doc).get("job") or {}).get("descriptionHtml")
    if not html:
        return None
    return _to_markdown(BeautifulSoup(html, "html.parser")) or None


ADAPTER: dict[str, Any] = {
    "company_name": _waas_company,
    "location": _waas_location,
    "description": _waas_description,
}
