"""Unit tests for the Generalist AI (generalistai.com) adapter — the job body
has multiple <h1> section headings ("About Generalist", "About the Role")
alongside the real job title, so title is pinned to the dedicated
h1.job-title element rather than relying on DOM-order luck; location lives
in a metadata table row instead of a location-labeled element.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_GENERALIST_URL = "https://generalistai.com/careers/software-engineer-infrastructure"


def test_parse_html_generalist_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generalist_job.html")
    result = parse_html(html, _GENERALIST_URL)
    assert result["title"] == "Software Engineer: Infrastructure"


def test_parse_html_generalist_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generalist_job.html")
    result = parse_html(html, _GENERALIST_URL)
    assert result["location"] == "San Francisco (SFO) or Boston (BOS)"


def test_parse_html_generalist_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generalist_job.html")
    result = parse_html(html, _GENERALIST_URL)
    assert result["description"] is not None
    assert "general intelligence for the physical world" in result["description"]
