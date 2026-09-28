"""Unit tests for the HeyGen (heygen.com) adapter — custom Next.js careers
site whose location sits in the h1's next sibling div, and whose description
lives in a CSS-module-hashed "greenhouse-content-module__*__content" div.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_HEYGEN_URL = "https://www.heygen.com/careers/4172070007"


def test_parse_html_heygen_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("heygen_job.html")
    result = parse_html(html, _HEYGEN_URL)
    assert result["title"] == "Backend Engineer"


def test_parse_html_heygen_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("heygen_job.html")
    result = parse_html(html, _HEYGEN_URL)
    assert result["company_name"] == "HeyGen"


def test_parse_html_heygen_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("heygen_job.html")
    result = parse_html(html, _HEYGEN_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_heygen_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("heygen_job.html")
    result = parse_html(html, _HEYGEN_URL)
    assert result["description"] is not None
    assert "core systems and infrastructure" in result["description"]
