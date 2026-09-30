"""Unit tests for the Mercor (mercor.com) site adapter — Next.js page with an empty
body; every job (Ashby-sourced) lives in the __NEXT_DATA__ JSON blob's `jobs` list,
so the adapter picks the one whose id matches the URL.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_MERCOR_URL = "https://www.mercor.com/careers/4f4fc8c3-4056-47bb-9e00-1db6e5dd958f/"


def test_parse_html_mercor_location_matches_job_id() -> None:
    from jobforce.services.parse import parse_html

    html = _read("mercor_job.html")
    result = parse_html(html, _MERCOR_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_mercor_location_other_job() -> None:
    from jobforce.services.parse import parse_html

    html = _read("mercor_job.html")
    url = "https://www.mercor.com/careers/f6035e89-f820-482c-9500-efb70226b134/"
    assert parse_html(html, url)["location"] == "New York City"


def test_parse_html_mercor_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("mercor_job.html")
    result = parse_html(html, _MERCOR_URL)
    assert result["description"] is not None
    assert "build agentic products that scale" in result["description"]
    assert "NYC role body" not in result["description"]


def test_parse_html_mercor_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("mercor_job.html")
    result = parse_html(html, _MERCOR_URL)
    assert result["role_type"] == "full-time"
