# ---------------------------------------------------------------------------
# Grid Dynamics (griddynamics.com/careers/vacancy/<id>) — title extracts fine
# via the generic adapter; location isn't exposed via any plain element the
# generic adapter checks, and the generic adapter's description falls back
# to the short <meta name="description"> tag, dropping the "Essential
# functions"/requirements lists present in the full vacancy body.
# ---------------------------------------------------------------------------

from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from .._common import _text, _to_markdown

HOSTNAME = "griddynamics.com"


def _griddynamics_location(doc: BeautifulSoup, url: str) -> str | None:
    return _text(doc.select_one(".careers-vacancy__underline-text"))


def _griddynamics_description(doc: BeautifulSoup, url: str) -> str | None:
    return _to_markdown(doc.select_one(".careers-vacancy__content-block"))


ADAPTER: dict[str, Any] = {
    "location": _griddynamics_location,
    "description": _griddynamics_description,
}
