"""Unit tests for the Work at a Startup (workatastartup.com) adapter — Inertia app; job data lives in the JSON ``data-page`` attribute."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WAAS_URL = "https://www.workatastartup.com/jobs/93490"


def test_parse_html_workatastartup_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("workatastartup_job.html"), _WAAS_URL)
    assert result["company_name"] == "VOYGR"


def test_parse_html_workatastartup_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("workatastartup_job.html"), _WAAS_URL)
    assert result["location"] == "San Francisco, CA, US"


def test_parse_html_workatastartup_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("workatastartup_job.html"), _WAAS_URL)
    assert result["description"] is not None
    assert "real-world index" in result["description"]
    assert "Product-minded" in result["description"]
