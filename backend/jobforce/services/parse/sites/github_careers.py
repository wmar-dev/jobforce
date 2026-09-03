# ---------------------------------------------------------------------------
# GitHub (www.github.careers/careers-home/jobs/<id>) — a Phenom People/iCIMS
# board (same "#header-locations" element id seen on careers.docusign.com).
# title and description already extract fine via the generic adapter; the
# page <title> is "<role> in <location> | GitHub, Inc." so company_name
# needs a fixed override, and location isn't exposed via any plain element
# the generic adapter checks.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "github.careers"


def _github_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one("#header-locations"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "GitHub",
    "location": _github_location,
}
