"""Unit tests for the Lever (jobs.lever.co/<company>/<id>) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_lever_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["title"] == "AI Engineer, Product"


def test_parse_html_lever_company_from_title_tag() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["company_name"] == "Mistral AI"


def test_parse_html_lever_location_first_category() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["location"] == "Paris"


def test_parse_html_lever_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["role_type"] == "full-time"


def test_parse_html_lever_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["description"] is not None
    assert "Mistral" in result["description"]
