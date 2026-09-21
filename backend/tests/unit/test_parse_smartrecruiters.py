"""Unit tests for the SmartRecruiters (jobs.smartrecruiters.com) adapter — the
DOM has a hidden "IE11 no longer supported" dialog whose own <h1> precedes the
real job-title <h1> in document order, so the generic adapter's bare
`doc.select_one("h1")` grabs the wrong one."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SMARTRECRUITERS_URL = (
    "https://jobs.smartrecruiters.com/ASML1/743999885046533-field-service-engineer-exe-hina"
)


def test_parse_html_smartrecruiters_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("smartrecruiters_job.html")
    result = parse_html(html, _SMARTRECRUITERS_URL)
    assert result["title"] == "Field Service Engineer EXE/HiNA"


def test_parse_html_smartrecruiters_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("smartrecruiters_job.html")
    result = parse_html(html, _SMARTRECRUITERS_URL)
    assert result["company_name"] == "ASML"


def test_parse_html_smartrecruiters_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("smartrecruiters_job.html")
    result = parse_html(html, _SMARTRECRUITERS_URL)
    assert result["location"] == "Hillsboro, OR, USA"


def test_parse_html_smartrecruiters_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("smartrecruiters_job.html")
    result = parse_html(html, _SMARTRECRUITERS_URL)
    assert result["description"] is not None
    assert "Competency Engineers" in result["description"]


def test_parse_html_smartrecruiters_posted_at() -> None:
    # Not a smartrecruiters.py override — the generic adapter's posted_at
    # extractor already picks up meta[itemprop="datePosted"].
    from jobforce.services.parse import parse_html

    html = _read("smartrecruiters_job.html")
    result = parse_html(html, _SMARTRECRUITERS_URL)
    assert result["posted_at"] == "2023-02-09"
