# ---------------------------------------------------------------------------
# Renaissance Philanthropy (renaissancephilanthropy.org) — Squarespace site
# with no <h1> anywhere on a job page, so the generic adapter falls all the
# way back to the raw <title> tag (which is "<job title> — <full site
# tagline>", joined with unicode em/en dashes the generic ASCII "-"/"|"
# stripping regex doesn't match). The real title is the first h2.preFade in
# the page content, sometimes suffixed "at Renaissance Philanthropy" — strip
# that. Postings don't have a dedicated location field; a "This position is
# <phrase>." blurb sits in the <p> immediately before the "About Renaissance
# Philanthropy" <h3>, which is present on every posting.
# ---------------------------------------------------------------------------

from __future__ import annotations

import re
from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "renaissancephilanthropy.org"

_TITLE_SUFFIX_RE = re.compile(r"\s+at Renaissance Philanthropy$", re.IGNORECASE)
_LOCATION_BLURB_RE = re.compile(r"^This position is (.*?)\.", re.IGNORECASE)


def _rp_title(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("h2.preFade")
    text = _text(el)
    if not text:
        return None
    return _TITLE_SUFFIX_RE.sub("", text).strip() or None


def _rp_location(doc: BeautifulSoup, url: str) -> str | None:
    heading = doc.find("h3", string="About Renaissance Philanthropy")
    if heading is None:
        return None
    blurb = _text(heading.find_previous_sibling("p")) or ""
    m = _LOCATION_BLURB_RE.match(blurb)
    if not m:
        return None
    phrase = m.group(1).strip()
    return "Remote" if "remote" in phrase.lower() else phrase.capitalize()


def _rp_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("main#page"))


ADAPTER: dict[str, Any] = {
    "title": _rp_title,
    "company_name": lambda doc, url: "Renaissance Philanthropy",
    "location": _rp_location,
    "description": _rp_description,
}
