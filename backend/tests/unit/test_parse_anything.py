"""Unit tests for the Anything (create.xyz, rebranded from Create) adapter —
the page has a stray content <h1> ("What this role is") below the real job
title, which lives in an <h2>, so the generic h1-first title lookup grabs
the wrong heading.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ANYTHING_URL = "https://www.create.xyz/careers/f4123aa5-855a-4b82-b762-66fb4a77f493"


def test_parse_html_anything_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anything_job.html")
    result = parse_html(html, _ANYTHING_URL)
    assert result["title"] == "Backend Engineer - AI"


def test_parse_html_anything_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anything_job.html")
    result = parse_html(html, _ANYTHING_URL)
    assert result["company_name"] == "Anything"


def test_parse_html_anything_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anything_job.html")
    result = parse_html(html, _ANYTHING_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_anything_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anything_job.html")
    result = parse_html(html, _ANYTHING_URL)
    assert result["description"] is not None
    assert "AI product engineer for the next wave of entrepreneurs" in result["description"]
