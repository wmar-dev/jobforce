"""Unit tests for the Pinterest (pinterestcareers.com) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_pinterest_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["title"] == "Staff Machine Learning Engineer, Ads Conversion"


def test_parse_html_pinterest_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["company_name"] == "Pinterest"


def test_parse_html_pinterest_location_from_first_li() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["location"] == "San Francisco / Palo Alto / Seattle"


def test_parse_html_pinterest_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["role_type"] == "full-time"


def test_parse_html_pinterest_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["description"] is not None
    assert "Machine Learning" in result["description"]
