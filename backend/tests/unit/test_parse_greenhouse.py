"""Unit tests for the Greenhouse (boards/job-boards.greenhouse.io) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# parse_html — Greenhouse adapter (boards.greenhouse.io)
# ---------------------------------------------------------------------------


def test_parse_html_greenhouse_company_from_url_path() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["company_name"] == "Stripe"


def test_parse_html_greenhouse_location_from_dom() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["location"] == "San Francisco, CA"


def test_parse_html_greenhouse_title_from_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["title"] == "Staff Engineer"


def test_parse_html_greenhouse_job_boards_subdomain() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/stripe/jobs/12345")
    assert result["company_name"] == "Stripe"


def test_parse_html_greenhouse_detects_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["role_type"] == "full-time"


# ---------------------------------------------------------------------------
# parse_html — Anthropic via job-boards.greenhouse.io
# ---------------------------------------------------------------------------


def test_parse_html_anthropic_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["title"] == "Research Engineer, Interpretability"


def test_parse_html_anthropic_company_from_url_path() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["company_name"] == "Anthropic"


def test_parse_html_anthropic_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["location"] == "San Francisco, CA"


def test_parse_html_anthropic_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["description"] is not None
    assert "interpretability" in result["description"].lower()


def test_parse_html_anthropic_role_type_none_for_vevraa_boilerplate() -> None:
    # "government contractor" in VEVRAA boilerplate must not match — word boundary
    # check on \bcontract\b excludes "contractor".
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["role_type"] is None
