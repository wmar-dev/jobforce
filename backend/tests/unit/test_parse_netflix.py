"""Unit tests for the Netflix (explore.jobs.netflix.net) site adapter — an
Eightfold-powered ATS. Title and description already extract correctly via
the generic adapter (no hydration race observed), but company_name picks up
the wrong value from `og:site_name` ("Careers at Netflix" instead of
"Netflix") and location is null because the page's `.position-location`
class doesn't match the generic `.job-location, .location` selector.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_NETFLIX_URL = "https://explore.jobs.netflix.net/careers/job/790314330968"


def test_parse_html_netflix_company_overrides_site_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netflix_job.html")
    result = parse_html(html, _NETFLIX_URL)
    assert result["company_name"] == "Netflix"


def test_parse_html_netflix_location_strips_more_link() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netflix_job.html")
    result = parse_html(html, _NETFLIX_URL)
    assert (
        result["location"]
        == "Los Gatos, California, United States of America • New York, New York, United States of America"
    )


def test_parse_html_netflix_title_via_generic_adapter() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netflix_job.html")
    result = parse_html(html, _NETFLIX_URL)
    assert result["title"] == "Machine Learning Engineer 5 - Ads Inventory Management & Forecasting"


def test_parse_html_netflix_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netflix_job.html")
    result = parse_html(html, _NETFLIX_URL)
    assert result["description"] is not None
    assert "Ads Platform Engineering teams" in result["description"]
