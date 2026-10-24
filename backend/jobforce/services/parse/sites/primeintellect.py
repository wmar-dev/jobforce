# ---------------------------------------------------------------------------
# Prime Intellect (primeintellect.ai) — Next.js careers page. Facts sit in a
# <dl> inside the aside (Team / Location / Commitment, each a <div> of dt+dd);
# the role body is the <article> prose block. CSS module class names carry a
# hash suffix, so match on the stable "careers_prose" prefix.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "primeintellect.ai"


def _pi_location(doc: BeautifulSoup, url: str) -> str | None:
    for dt in doc.select("aside dl dt"):
        if _text(dt) == "Location":
            return _text(dt.find_next_sibling("dd"))
    return None


def _pi_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one('article[class*="careers_prose"]'))


ADAPTER: dict[str, Any] = {
    "location": _pi_location,
    "description": _pi_description,
}
