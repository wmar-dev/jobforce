"""Unit tests for the Databricks (databricks.com) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_databricks_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["title"] == "Senior Software Engineer - Backend"


def test_parse_html_databricks_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["company_name"] == "Databricks"


def test_parse_html_databricks_location_strips_apply_button() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["location"] == "San Francisco, CA"


def test_parse_html_databricks_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["description"] is not None
    assert "distributed" in result["description"].lower()


def test_parse_html_databricks_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["role_type"] == "full-time"
