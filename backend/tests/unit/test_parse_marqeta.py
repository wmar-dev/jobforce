"""Unit tests for the Marqeta (marqeta.com) adapter — custom Next.js careers
page (not an ashbyhq.com URL, though "Apply now" posts to Ashby). Company
name and og:site_name are both absent from the markup, and the location
lives in an unlabelled sidebar div among sibling divs with identical
classes, distinguished only by a nested sub-label span.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_MARQETA_URL = "https://www.marqeta.com/careers/5eaf1f0e-1359-458f-899b-05e374c9ec0b"


def test_parse_html_marqeta_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("marqeta_job.html")
    result = parse_html(html, _MARQETA_URL)
    assert result["title"] == "Senior Production Support Engineer"


def test_parse_html_marqeta_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("marqeta_job.html")
    result = parse_html(html, _MARQETA_URL)
    assert result["company_name"] == "Marqeta"


def test_parse_html_marqeta_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("marqeta_job.html")
    result = parse_html(html, _MARQETA_URL)
    assert result["location"] == "Remote - USA"


def test_parse_html_marqeta_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("marqeta_job.html")
    result = parse_html(html, _MARQETA_URL)
    assert result["description"] is not None
    assert "Senior Production Support Engineer" in result["description"]
    assert "Flexible First" in result["description"]
