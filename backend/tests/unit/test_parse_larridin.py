"""Unit tests for the Larridin (larridin.com) site adapter — HubSpot CMS page;
company name, location, and description all live in custom markup with no
generic-adapter hooks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_LARRIDIN_URL = "https://larridin.com/software-engineer"


def test_parse_html_larridin_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("larridin_job.html")
    result = parse_html(html, _LARRIDIN_URL)
    assert result["company_name"] == "Larridin"


def test_parse_html_larridin_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("larridin_job.html")
    result = parse_html(html, _LARRIDIN_URL)
    assert result["location"] == "Bay Area | In-Office"


def test_parse_html_larridin_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("larridin_job.html")
    result = parse_html(html, _LARRIDIN_URL)
    assert result["description"] is not None
    assert "AI-native engineering teams that own outcomes" in result["description"]
