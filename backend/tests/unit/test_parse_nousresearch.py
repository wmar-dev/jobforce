"""Unit tests for the Nous Research (nousresearch.com) adapter — Next.js catalogue page with a fixed company name and eyebrow line ("Full time, Remote") holding the location."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_NOUS_URL = "https://nousresearch.com/careers/software-engineer"


def test_parse_html_nousresearch_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nousresearch_job.html")
    result = parse_html(html, _NOUS_URL)
    assert result["title"] == "Software Engineer"


def test_parse_html_nousresearch_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nousresearch_job.html")
    result = parse_html(html, _NOUS_URL)
    assert result["company_name"] == "Nous Research"


def test_parse_html_nousresearch_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nousresearch_job.html")
    result = parse_html(html, _NOUS_URL)
    assert result["location"] == "Remote"


def test_parse_html_nousresearch_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nousresearch_job.html")
    result = parse_html(html, _NOUS_URL)
    assert result["description"] is not None
    assert "Hermes Agent" in result["description"]
    assert "Responsibilities" in result["description"]
