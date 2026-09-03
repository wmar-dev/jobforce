# ---------------------------------------------------------------------------
# Warner Bros. Discovery site adapter — careers.wbd.com (Phenom People ATS)
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careers.wbd.com"


def _wbd_location(doc: BeautifulSoup, url: str) -> str | None:
    # Multi-location postings list one .location element per location; a plain
    # select_one would only capture the first, dropping the rest.
    seen: list[str] = []
    for el in doc.select(".location.au-target"):
        if (t := _text(el)) and t not in seen:
            seen.append(t)
    return "; ".join(seen) if seen else None


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Warner Bros. Discovery",
    "location": _wbd_location,
    "description": lambda doc, url: _to_markdown(doc.select_one(".jd-info")),
}
