# ---------------------------------------------------------------------------
# Chime (careers.chime.com/jobs/<id>/<slug>) — title extracts fine via the
# generic adapter's <h1>. Location is the second of two <p> tags inside
# ".content-wrapper" (department, then location); description lives in the
# ".jobCopy" container.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "careers.chime.com"


def _chime_location(doc: BeautifulSoup, url: str) -> str | None:
    ps = doc.select(".content-wrapper p")
    if len(ps) < 2:
        return None
    return _text(ps[1])


def _chime_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".jobCopy"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Chime",
    "location": _chime_location,
    "description": _chime_description,
}
