# ---------------------------------------------------------------------------
# ArgusEye (arguseye.ai) — custom Next.js page. The job header holds a <dl> of
# <dt>/<dd> pairs (Department, Location, Type, Posted); the job body lives in
# a ".detail-content" div.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "arguseye.ai"


def _arguseye_location(doc: BeautifulSoup, url: str) -> str | None:
    for dt in doc.select("dl dt"):
        if dt.get_text(strip=True).lower() == "location":
            return _text(dt.find_next_sibling("dd"))
    return None


def _arguseye_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".detail-content"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "ArgusEye",
    "location": _arguseye_location,
    "description": _arguseye_description,
}
