# ---------------------------------------------------------------------------
# HeyGen (heygen.com) — company's own custom careers site (Next.js). Title
# comes through fine via the generic adapter's <h1>, but there is no
# og:site_name/footer copyright to derive company_name from, so it's fixed.
# Location is a plain div immediately following the <h1>. The description
# lives in a div whose class is a CSS-module-hashed
# "greenhouse-content-module__<hash>__content" — match by prefix/suffix
# since the hash segment can change between site deploys.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup, Tag

from .._common import _text, _to_markdown

HOSTNAME = "heygen.com"

_CONTENT_MODULE_RE = re.compile(r"^greenhouse-content-module__\w+__content$")


def _heygen_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.find("h1")
    if not isinstance(h1, Tag):
        return None
    loc_div = h1.find_next_sibling("div")
    return _text(loc_div)


def _heygen_description(doc: BeautifulSoup, url: str) -> str | None:
    container = next(
        (
            div
            for div in doc.find_all("div")
            if any(_CONTENT_MODULE_RE.match(c) for c in (div.get("class") or []))
        ),
        None,
    )
    return _to_markdown(container)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "HeyGen",
    "location": _heygen_location,
    "description": _heygen_description,
}
