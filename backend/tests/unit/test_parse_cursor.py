"""Unit tests for the Cursor (cursor.com/careers/<slug>) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_cursor_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["title"] == "Software Engineer, ML Infrastructure"


def test_parse_html_cursor_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["company_name"] == "Cursor"


def test_parse_html_cursor_location_from_header_p() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["location"] == "San Francisco; New York"


def test_parse_html_cursor_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["description"] is not None
    assert "ML Infrastructure" in result["description"]


def test_parse_html_cursor_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["role_type"] == "full-time"
