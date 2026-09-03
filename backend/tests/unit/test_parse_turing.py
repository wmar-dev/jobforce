"""Unit tests for the Turing (careers.turing.com/job/<id>) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_TURING_URL = "https://careers.turing.com/job/5609732004"


def test_parse_html_turing_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert result["company_name"] == "Turing"


def test_parse_html_turing_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert result["title"] == "Forward Deployed AI Engineer"


def test_parse_html_turing_location_strips_prefix() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert (
        result["location"]
        == "New York, New York, United States; San Francisco, California, United States"
    )


def test_parse_html_turing_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert result["description"] is not None
    assert "Generative AI" in result["description"]
