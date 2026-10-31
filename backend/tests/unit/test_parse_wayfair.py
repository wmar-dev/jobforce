"""Unit tests for the Wayfair (www.wayfair.com/careers) adapter — job metadata
lives in a `<dl class="CareersJobDetailsDisplayDescription-list">` of
`Location:` / `Category:` term pairs (no `.location` class), and the body sits
in `.CareersJobDetailsDisplayDescription-jobDescription` (no lowercase
"description" in its class name, so the generic selector misses it).
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WAYFAIR_URL = (
    "https://www.wayfair.com/careers/job/principal-software-engineer--customer-tech/2-19647"
)


def test_parse_html_wayfair_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wayfair_job.html")
    result = parse_html(html, _WAYFAIR_URL)
    assert result["location"] == "Mountain View, California"


def test_parse_html_wayfair_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wayfair_job.html")
    result = parse_html(html, _WAYFAIR_URL)
    assert result["description"] is not None
    assert "Customer Tech organization" in result["description"]
