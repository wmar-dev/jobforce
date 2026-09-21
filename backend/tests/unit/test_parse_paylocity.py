"""Unit tests for the Paylocity Recruiting (recruiting.paylocity.com) adapter.
The <title> tag reads "<Company> - <Job Title>" — the reverse order the
generic adapter's title-tag fallback assumes — so title and company_name both
need overrides even though a title-tag heuristic exists generically."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_PAYLOCITY_URL = "https://recruiting.paylocity.com/Recruiting/Jobs/Details/4391637"


def test_parse_html_paylocity_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paylocity_job.html")
    result = parse_html(html, _PAYLOCITY_URL)
    assert result["title"] == "Ecosystem Partner Director"


def test_parse_html_paylocity_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paylocity_job.html")
    result = parse_html(html, _PAYLOCITY_URL)
    assert result["company_name"] == "Axim Collaborative Inc."


def test_parse_html_paylocity_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paylocity_job.html")
    result = parse_html(html, _PAYLOCITY_URL)
    assert result["location"] == "Hybrid Remote • Cambridge, MA"


def test_parse_html_paylocity_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paylocity_job.html")
    result = parse_html(html, _PAYLOCITY_URL)
    assert result["description"] is not None
    assert "ABOUT AXIM COLLABORATIVE" in result["description"]
