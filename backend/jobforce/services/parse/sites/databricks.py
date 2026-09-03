# ---------------------------------------------------------------------------
# Databricks site adapter — databricks.com/company/careers/...
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "databricks.com"


def _databricks_location(doc: BeautifulSoup, url: str) -> str | None:
    h1 = doc.select_one("h1")
    if h1:
        sib = h1.find_next_sibling()
        if sib:
            # Remove the "Apply now" button text
            for btn in sib.find_all("button"):
                btn.decompose()
            return _text(sib)
    return None


def _databricks_description(doc: BeautifulSoup, url: str) -> str | None:
    el = doc.select_one("main")
    return _to_markdown(el)


ADAPTER: dict[str, Any] = {
    "company_name": lambda doc, url: "Databricks",
    "location": _databricks_location,
    "description": _databricks_description,
}
