"""Unit tests for the Lane (getonlane.com) adapter — Next.js careers page with a
schema.org JobPosting JSON-LD block and no og:site_name / description class hooks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_LANE_URL = "https://www.getonlane.com/careers/founding-backend-engineer"


def test_parse_html_lane_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("lane_job.html"), _LANE_URL)
    assert result["company_name"] == "Lane"


def test_parse_html_lane_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("lane_job.html"), _LANE_URL)
    assert result["location"] == "San Francisco, CA"


def test_parse_html_lane_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("lane_job.html"), _LANE_URL)
    assert result["description"] is not None
    assert "money-path logic" in result["description"]
