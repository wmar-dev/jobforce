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


def test_parse_html_google_careers_description_strips_icon_and_dismiss_chrome() -> None:
    from jobforce.services.parse import parse_html

    callout = (
        '<div class="callout"><div role="img" aria-label="Info">'
        '<i class="google-material-icons notranslate" aria-hidden="true">info_outline</i></div>'
        '<span aria-hidden="true">X</span>'
        "<span>In most instances, this position requires in-person interviews.</span></div>"
    )
    html = _read("google_careers_job.html").replace(
        '<div class="KwJkGe">', f'<div class="xbCN0b">{callout}</div><div class="KwJkGe">', 1
    )
    description = parse_html(html, _GOOGLE_CAREERS_URL)["description"] or ""
    assert "info" not in description.lower().replace("information", "")
    assert not description.lstrip().startswith("X")
    assert "in-person interviews" in description
