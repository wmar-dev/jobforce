"""Unit tests for the Workday (*.myworkdayjobs.com) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_workday_title_from_automation_id() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["title"] == "Senior Software Engineer"


def test_parse_html_workday_location_from_automation_id() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["location"] == "Austin, TX"


def test_parse_html_workday_company_from_subdomain() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["company_name"] == "Acme"


def test_parse_html_workday_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["description"] is not None
    assert "platform" in result["description"].lower()


def test_parse_html_workday_title_falls_back_to_job_posting_header() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job_dl_locations.html")
    result = parse_html(
        html,
        "https://verily.wd1.myworkdayjobs.com/en-US/Verily_Careers/job/San-Bruno-California/Staff-AI-Applied-Scientist_REQ-723",
    )
    assert result["title"] == "Staff AI Applied Scientist"


def test_parse_html_workday_location_falls_back_to_dl_dd_list() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job_dl_locations.html")
    result = parse_html(
        html,
        "https://verily.wd1.myworkdayjobs.com/en-US/Verily_Careers/job/San-Bruno-California/Staff-AI-Applied-Scientist_REQ-723",
    )
    assert (
        result["location"]
        == "San Bruno, California; Boston, Massachusetts; Mountain View, California"
    )


def test_parse_html_workday_suffix_match_applies_adapter() -> None:
    from jobforce.services.parse import SITE_ADAPTERS, _match_adapter

    assert "myworkdayjobs.com" in SITE_ADAPTERS
    assert _match_adapter("acme.wd1.myworkdayjobs.com") is SITE_ADAPTERS["myworkdayjobs.com"]
