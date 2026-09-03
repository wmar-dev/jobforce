"""Unit tests for the Breezy HR (<company>.breezy.hr/p/<id>-<slug>) site adapter
— shared ATS. The page has two <h1>s (site brand logo, then the real job
title), so the generic adapter's bare "h1" selector picks up the wrong one.
Company name is derived from the subdomain, same pattern as the Workday
adapter.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BREEZY_BEARROBOTICS_URL = "https://bear-robotics.breezy.hr/p/58d3df356ee1-software-engineer-ii"


def test_parse_html_breezy_title_ignores_brand_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["title"] == "Software Engineer II"


def test_parse_html_breezy_company_from_subdomain() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["company_name"] == "Bear Robotics"


def test_parse_html_breezy_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["location"] == "Redwood City, CA"


def test_parse_html_breezy_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["description"] is not None
    assert "designing, developing, and maintaining complex software" in result["description"]
