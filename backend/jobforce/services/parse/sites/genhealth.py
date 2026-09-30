# ---------------------------------------------------------------------------
# GenHealth.ai (genhealth.ai) — custom Next.js careers page. No company name
# or JobPosting JSON-LD in the markup; the job body lives in an
# "article.cmscontent" block. The page does not state a location.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _to_markdown

HOSTNAME = "genhealth.ai"


def _genhealth_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one("article.cmscontent"))


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "GenHealth.ai",
    "description": _genhealth_description,
}
