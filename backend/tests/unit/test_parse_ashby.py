"""Unit tests for the Ashby (jobs.ashbyhq.com) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_ashby_title_from_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["title"] == "Principal Engineer"


def test_parse_html_ashby_company_from_url_path() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["company_name"] == "Figma"


def test_parse_html_ashby_location_from_brief_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["location"] == "New York, NY"


def test_parse_html_ashby_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["description"] is not None
    assert "design" in result["description"].lower()


def test_parse_html_ashby_hyphenated_company_capitalized() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/linear-app/xyz-456")
    assert result["company_name"] == "Linear App"


def test_parse_html_ashby_frontcareers_slug_maps_to_front() -> None:
    """Front's Ashby board slug is 'frontcareers', not 'front'."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/frontcareers/xyz-456")
    assert result["company_name"] == "Front"


def test_parse_html_ashby_grammarly_slug_maps_to_grammarly() -> None:
    """Grammarly's Ashby board slug is its parent brand's legal entity name,
    URL-encoded with spaces (%20) since it contains real spaces."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/Superhuman%20Platform%20Inc/xyz-456")
    assert result["company_name"] == "Grammarly"


def test_parse_html_ashby_url_encoded_slug_decoded_before_capitalizing() -> None:
    """A %20-encoded slug with no override should still decode to real words
    rather than leaking literal '%20' into the capitalized company name."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/Acme%20Corp/xyz-456")
    assert result["company_name"] == "Acme Corp"


# ---------------------------------------------------------------------------
# parse_html — Ashby new markup (ashby_decagon_job.html)
# Fixture captured from jobs.ashbyhq.com/decagon when location was returning
# None due to Ashby renaming .ashby-job-posting-brief-description-item to
# a left-pane labeled-section layout (<h2>Location</h2><p>…</p>).
# ---------------------------------------------------------------------------


def test_parse_html_ashby_new_markup_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["title"] == "Senior Software Engineer, Agent Orchestration"


def test_parse_html_ashby_new_markup_company_from_url() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["company_name"] == "Decagon"


def test_parse_html_ashby_new_markup_location_from_labeled_section() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["location"] == "San Francisco"


def test_parse_html_ashby_new_markup_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["description"] is not None
    assert "orchestration" in result["description"].lower()


def test_parse_html_ashby_old_markup_location_still_works() -> None:
    """Fallback to legacy .ashby-job-posting-brief-description-item still works."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["location"] == "New York, NY"
