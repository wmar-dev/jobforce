"""Unit tests for the Bright Data (brightdata.com) adapter — WordPress careers pages
whose <title> is the generic "Careers | ..." string; real data lives in .single_pos.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BRIGHTDATA_URL = "https://brightdata.com/careers/senior-backend-javascript-developer-san-francisco"


def test_parse_html_brightdata_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("brightdata_job.html"), _BRIGHTDATA_URL)
    assert result["company_name"] == "Bright Data"


def test_parse_html_brightdata_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("brightdata_job.html"), _BRIGHTDATA_URL)
    assert result["location"] == "US, San Francisco (Hybrid)"


def test_parse_html_brightdata_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("brightdata_job.html"), _BRIGHTDATA_URL)
    assert result["description"] is not None
    assert "back-end JavaScript developers" in result["description"]
    assert "Back to careers page" not in result["description"]


def test_parse_html_brightdata_location_remote_strips_empty_prefix() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brightdata_job.html").replace("US, San Francisco (Hybrid)", ", (Remote)")
    result = parse_html(html, _BRIGHTDATA_URL)
    assert result["location"] == "(Remote)"
