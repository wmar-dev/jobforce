"""Unit tests for the Rippling ATS (ats.rippling.com/<company-slug>/jobs/<id>)
site adapter — shared job board used by many companies (e.g. ThoughtSpot,
Rippling itself). The recruiter-authored description HTML sometimes embeds the
next section's heading inside the same malformed <h1> as the job title, so
title comes from the document <title> tag instead. There's no structured
company name field on the job page; it's derived from the breadcrumb link back
to the employer's own careers site.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_RIPPLING_THOUGHTSPOT_URL = (
    "https://ats.rippling.com/thoughtspot/jobs/602db28c-e76f-4fee-ad02-0419372d02af"
)


def test_parse_html_rippling_title_ignores_embedded_next_heading() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["title"] == "Staff Forward Deployment Engineer"


def test_parse_html_rippling_company_from_breadcrumb() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["company_name"] == "Thoughtspot"


def test_parse_html_rippling_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["location"] == "Mountain View, CA"


def test_parse_html_rippling_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["description"] is not None
    assert "Agentic Analytics Platform" in result["description"]
