"""Unit tests for the Dayforce (*.dayforcehcm.com) adapter. The SPA's
`data-testid` job-detail elements are unreliable (present right after
hydration, gone on a later read of the same page), so description comes from
the stable server-rendered `<meta name="description">` tag instead, and
company_name from the URL's tenant path segment (no per-tenant company
element exists in the DOM)."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_DAYFORCE_URL = "https://jobs.dayforcehcm.com/en-US/mydayforce/alljobs/jobs/102503"


def test_parse_html_dayforce_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("dayforce_job.html")
    result = parse_html(html, _DAYFORCE_URL)
    assert result["company_name"] == "Mydayforce"


def test_parse_html_dayforce_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("dayforce_job.html")
    result = parse_html(html, _DAYFORCE_URL)
    assert result["description"] is not None
    assert "Payroll Onboarding Consultant within Dayforce Managed Services" in result["description"]
