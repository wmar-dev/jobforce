"""Unit tests for the DoorDash (careersatdoordash.com/jobs/<slug>/<id>) site
adapter — title and company_name already extract fine via the generic adapter;
location and description need dedicated selectors ("#jd-location" and
".content").
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_DOORDASH_URL = "https://careersatdoordash.com/jobs/software-engineer-data-and-ai-platform/8171620"


def test_parse_html_doordash_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("doordash_job.html")
    result = parse_html(html, _DOORDASH_URL)
    assert result["title"] == "SOFTWARE ENGINEER, DATA AND AI PLATFORM"


def test_parse_html_doordash_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("doordash_job.html")
    result = parse_html(html, _DOORDASH_URL)
    assert result["location"] == "San Francisco, CA; Sunnyvale, CA"


def test_parse_html_doordash_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("doordash_job.html")
    result = parse_html(html, _DOORDASH_URL)
    assert result["description"] is not None
    assert "drill-down and cross-filter semantics" in result["description"]
