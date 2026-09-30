"""Unit tests for the Fleet (fleetai.com/careers/<slug>) adapter — Next.js page, no company element; name comes from the <title> suffix."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"

_FLEET_URL = "https://www.fleetai.com/careers/software-engineer"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_fleet_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("fleet_job.html"), _FLEET_URL)
    assert result["title"] == "Member of Technical Staff, Environment Generation"


def test_parse_html_fleet_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("fleet_job.html"), _FLEET_URL)
    assert result["company_name"] == "Fleet"


def test_parse_html_fleet_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("fleet_job.html"), _FLEET_URL)
    assert result["location"] == "San Francisco / New York"


def test_parse_html_fleet_description() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("fleet_job.html"), _FLEET_URL)
    assert result["description"] is not None
    assert "RL environments at scale" in result["description"]
