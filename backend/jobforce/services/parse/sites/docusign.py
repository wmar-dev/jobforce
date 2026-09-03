# ---------------------------------------------------------------------------
# Docusign (careers.docusign.com/careers-home/jobs/<id>) — title and
# description already extract fine via the generic adapter; the site's own
# og:site_name meta is buggy and echoes the full "<title> in <location> |
# careers-home" page title instead of "Docusign".
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text

HOSTNAME = "careers.docusign.com"


def _docusign_location(doc: BeautifulSoup, url: str) -> str | None:
    # "#job-location" only shows a single, seemingly arbitrary pick from a
    # multi-location posting (e.g. just "Seattle" for a job actually listed
    # in "San Francisco; Seattle"); "#header-locations" carries the full,
    # correct location list for both single- and multi-location postings.
    return _text(doc.select_one("#header-locations"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Docusign",
    "location": _docusign_location,
}
