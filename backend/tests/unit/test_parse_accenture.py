"""Unit tests for the Accenture (accenture.com) adapter — single-tenant AEM
page. Company name has no on-page element (fixed lambda); location lives in
a "Locations" accordion as one <p> per city, joined for multi-location roles.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ACCENTURE_URL = "https://www.accenture.com/us-en/careers/jobdetails?id=R00341833_en&title=AI+Native+Software+Engineer+-+Products"


def test_parse_html_accenture_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("accenture_job.html")
    result = parse_html(html, _ACCENTURE_URL)
    assert result["title"] == "AI Native Software Engineer - Products"


def test_parse_html_accenture_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("accenture_job.html")
    result = parse_html(html, _ACCENTURE_URL)
    assert result["company_name"] == "Accenture"


def test_parse_html_accenture_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("accenture_job.html")
    result = parse_html(html, _ACCENTURE_URL)
    assert (
        result["location"] == "Seattle, WA; Mountain View, CA; New York City, NY; San Francisco, CA"
    )


def test_parse_html_accenture_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("accenture_job.html")
    result = parse_html(html, _ACCENTURE_URL)
    assert result["description"] is not None
    assert "agentic software products" in result["description"]
