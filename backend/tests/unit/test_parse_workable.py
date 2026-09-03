"""Unit tests for the Workable (jobs/apply.workable.com) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_workable_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["title"] == "Senior Full-stack Software Engineer"


def test_parse_html_workable_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["company_name"] == "Kettle"


def test_parse_html_workable_location_with_remote() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["location"] == "San Francisco (Remote)"


def test_parse_html_workable_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["role_type"] == "full-time"


def test_parse_html_workable_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["description"] is not None
    assert "Kettle" in result["description"]


_WORKABLE_APPLY_URL = "https://apply.workable.com/innovaccer-analytics/j/643DCD9804/"


def test_parse_html_workable_apply_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_apply_innovaccer_job.html")
    result = parse_html(html, _WORKABLE_APPLY_URL)
    assert result["company_name"] == "Innovaccer Analytics"


def test_parse_html_workable_apply_location_handles_list_jobLocation() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_apply_innovaccer_job.html")
    result = parse_html(html, _WORKABLE_APPLY_URL)
    assert result["location"] == "San Francisco, California"


def test_parse_html_workable_apply_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_apply_innovaccer_job.html")
    result = parse_html(html, _WORKABLE_APPLY_URL)
    assert result["description"] is not None
    assert "production-grade AI systems" in result["description"]
