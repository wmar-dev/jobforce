"""Unit tests for the Eightfold (*.eightfold.ai) adapter — same ATS as
jobs.twilio.com (see test_parse_twilio.py), but multi-tenant: the static
<h1> always reads "Single Position", and there's no fixed company_name, so
it's parsed from the "<Job Title> | <Company>" <title> tag instead."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_EIGHTFOLD_URL = "https://lockheedmartin.eightfold.ai/careers/job/996476955847"


def test_parse_html_eightfold_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("eightfold_job.html")
    result = parse_html(html, _EIGHTFOLD_URL)
    assert result["title"] == "Financial Management - E2"


def test_parse_html_eightfold_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("eightfold_job.html")
    result = parse_html(html, _EIGHTFOLD_URL)
    assert result["company_name"] == "Lockheed Martin"


def test_parse_html_eightfold_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("eightfold_job.html")
    result = parse_html(html, _EIGHTFOLD_URL)
    assert result["location"] == "Titusville, FL"


def test_parse_html_eightfold_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("eightfold_job.html")
    result = parse_html(html, _EIGHTFOLD_URL)
    assert result["description"] is not None
    assert "EVM reporting" in result["description"]


def test_parse_html_eightfold_posted_at() -> None:
    from jobforce.services.parse import parse_html

    html = _read("eightfold_job.html")
    result = parse_html(html, _EIGHTFOLD_URL)
    assert result["posted_at"] == "2026-09-20"
