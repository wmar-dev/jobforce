"""Unit tests for the Whatnot (whatnot.com) adapter — custom Next.js careers
site with no og:site_name/footer to derive company_name from, and a
multi-office "Location" label/section-of-<p> pattern.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WHATNOT_URL = "https://www.whatnot.com/careers/roles/e3e7c019-4657-47a9-a9f3-123d2cd1a75e"


def test_parse_html_whatnot_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("whatnot_job.html")
    result = parse_html(html, _WHATNOT_URL)
    assert result["title"] == "Machine Learning Engineer, Growth"


def test_parse_html_whatnot_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("whatnot_job.html")
    result = parse_html(html, _WHATNOT_URL)
    assert result["company_name"] == "Whatnot"


def test_parse_html_whatnot_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("whatnot_job.html")
    result = parse_html(html, _WHATNOT_URL)
    assert result["location"] == "San Francisco, CA; New York, NY; Los Angeles, CA; Seattle, WA"


def test_parse_html_whatnot_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("whatnot_job.html")
    result = parse_html(html, _WHATNOT_URL)
    assert result["description"] is not None
    assert "recommendation and ranking systems" in result["description"]
