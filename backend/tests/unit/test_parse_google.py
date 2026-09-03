"""Unit tests for the Google Careers
(google.com/about/careers/applications/jobs/results/<slug>) site adapter.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_GOOGLE_CAREERS_URL = (
    "https://www.google.com/about/careers/applications/jobs/results/"
    "136775056809173702-senior-software-engineer-aiml-creative-intelligence"
)


def test_parse_html_google_careers_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["company_name"] == "Google"


def test_parse_html_google_careers_title_ignores_sitewide_heading() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["title"] == "Senior Software Engineer, AI/ML, Creative Intelligence"


def test_parse_html_google_careers_location_strips_icon_ligature() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["location"] == "Mountain View, CA, USA"


def test_parse_html_google_careers_description_excludes_boilerplate() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["description"] is not None
    assert "Generative AI" in result["description"]
    assert "Privacy Policy" not in result["description"]
    assert "equal opportunity" not in result["description"]
