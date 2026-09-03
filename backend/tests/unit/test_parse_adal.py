"""Unit tests for the AdaL (adalagent.ai) site adapter — custom React SPA."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ADAL_URL = "https://adalagent.ai/jobs/mts-production-quality"


def test_parse_html_adal_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["title"] == "Member of Technical Staff - Production Quality"


def test_parse_html_adal_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["company_name"] == "AdaL"


def test_parse_html_adal_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["location"] == "San Francisco, United States"


def test_parse_html_adal_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["description"] is not None
    assert "Production Quality" in result["description"]
