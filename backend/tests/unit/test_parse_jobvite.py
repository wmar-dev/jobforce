"""Unit tests for the Jobvite (jobs.jobvite.com) adapter — title, company_name,
location, and description all come from the page's schema.org JobPosting
JSON-LD block. The <title> tag reads "<Company> Careers - <Job Title>",
which the generic adapter's fallback mangles into just "<Company> Careers"."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_JOBVITE_URL = "https://jobs.jobvite.com/gigamon/job/oJJIAfwu"


def test_parse_html_jobvite_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("jobvite_job.html")
    result = parse_html(html, _JOBVITE_URL)
    assert result["title"] == "Senior Tax Analyst"


def test_parse_html_jobvite_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("jobvite_job.html")
    result = parse_html(html, _JOBVITE_URL)
    assert result["company_name"] == "Gigamon"


def test_parse_html_jobvite_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("jobvite_job.html")
    result = parse_html(html, _JOBVITE_URL)
    assert result["location"] == "Guindy, Chennai, Tamil Nadu, India"


def test_parse_html_jobvite_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("jobvite_job.html")
    result = parse_html(html, _JOBVITE_URL)
    assert result["description"] is not None
    assert "indirect tax returns" in result["description"]
