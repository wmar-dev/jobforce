"""Unit tests for the Kula (careers.kula.ai) adapter — location and
description come from the page's schema.org JobPosting JSON-LD block; title
and company_name already resolve via the generic adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_KULA_URL = "https://careers.kula.ai/cashfree/4467/"


def test_parse_html_kula_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("kula_job.html")
    result = parse_html(html, _KULA_URL)
    assert result["location"] == "Bellandur, Karnataka, India"


def test_parse_html_kula_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("kula_job.html")
    result = parse_html(html, _KULA_URL)
    assert result["description"] is not None
    assert "discover vulnerabilities" in result["description"]
