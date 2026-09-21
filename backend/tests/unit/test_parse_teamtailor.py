"""Unit tests for the Teamtailor (*.teamtailor.com) adapter — location and
description come from the page's schema.org JobPosting JSON-LD block, whose
`description` value is itself HTML-entity-escaped."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_TEAMTAILOR_URL = "https://deezer.teamtailor.com/jobs/7629174-design-system-manager-m-f-d"


def test_parse_html_teamtailor_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("teamtailor_job.html")
    result = parse_html(html, _TEAMTAILOR_URL)
    assert result["location"] == "Paris, FR"


def test_parse_html_teamtailor_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("teamtailor_job.html")
    result = parse_html(html, _TEAMTAILOR_URL)
    assert result["description"] is not None
    assert "Tempo" in result["description"]
