"""Unit tests for the Skydio (skydio.com) site adapter — Greenhouse-backed
careers pages rendered by Skydio's own site; company name, location, and
description live in custom markup with no generic-adapter hooks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SKYDIO_URL = (
    "https://www.skydio.com/jobs/cc83824e-a1cd-4bc7-9206-7264da9fbd61/"
    "?gh_jid=cc83824e-a1cd-4bc7-9206-7264da9fbd61"
)


def test_parse_html_skydio_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("skydio_job.html"), _SKYDIO_URL)
    assert result["company_name"] == "Skydio"


def test_parse_html_skydio_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("skydio_job.html"), _SKYDIO_URL)
    assert result["location"] == "San Mateo, California, United States"


def test_parse_html_skydio_description() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("skydio_job.html"), _SKYDIO_URL)
    assert result["description"] is not None
    assert "Train and deploy deep learning models" in result["description"]
