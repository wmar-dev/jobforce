"""Unit tests for the Atlassian (atlassian.com) site adapter — job header is a
".job-posting-detail--highlight" paragraph with pipe-separated "Team | Location |
Remote flag" text; description lives in the first ".column.colspan-10.text-left"
div inside the job-posting-detail section (a second, empty one follows it).
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ATLASSIAN_URL = "https://www.atlassian.com/company/careers/details/25809"


def test_parse_html_atlassian_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("atlassian_job.html")
    result = parse_html(html, _ATLASSIAN_URL)
    assert result["location"] == "Bengaluru, India"


def test_parse_html_atlassian_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("atlassian_job.html")
    result = parse_html(html, _ATLASSIAN_URL)
    assert result["description"] is not None
    assert "Jira Service Management (JSM)" in result["description"]


def test_parse_html_atlassian_placeholder_location_is_none() -> None:
    from jobforce.services.parse import parse_html

    html = _read("atlassian_placeholder_location_job.html")
    result = parse_html(html, "https://www.atlassian.com/company/careers/details/26578")
    assert result["location"] is None
