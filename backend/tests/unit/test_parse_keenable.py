"""Unit tests for the Keenable (app.keenable.ai) adapter — the page has a
hidden sitewide tagline <h1> ("Keenable — Search for AI agents") before the
real job title <h1>, so title is pinned to the CSS-modules title class;
location and employment type are combined in one "Full-time · Remote —
Worldwide" element and need splitting.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_KEENABLE_URL = "https://app.keenable.ai/careers/mts"


def test_parse_html_keenable_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("keenable_job.html")
    result = parse_html(html, _KEENABLE_URL)
    assert result["title"] == "Member of Technical Staff, Engineering"


def test_parse_html_keenable_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("keenable_job.html")
    result = parse_html(html, _KEENABLE_URL)
    assert result["location"] == "Remote — Worldwide"


def test_parse_html_keenable_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("keenable_job.html")
    result = parse_html(html, _KEENABLE_URL)
    assert result["description"] is not None
    assert "web search and knowledge access at web scale" in result["description"]
