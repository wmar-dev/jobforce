"""Unit tests for the Tetrate (careers.tetr8.io) adapter — Astro static page;
the h1 title and description blocks are siblings in one Tailwind column, and
the location is a trailing "<strong>Location:</strong> ..." prose paragraph.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_TETRATE_URL = "https://careers.tetr8.io/job/software-engineer-golang/"


def test_parse_html_tetrate_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("tetrate_job.html"), _TETRATE_URL)
    assert result["company_name"] == "Tetrate"


def test_parse_html_tetrate_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("tetrate_job.html"), _TETRATE_URL)
    assert result["location"] == "Remote (North America)"


def test_parse_html_tetrate_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("tetrate_job.html"), _TETRATE_URL)
    desc = result["description"]
    assert desc is not None
    assert "Golang and gRPC" in desc
    assert "## Responsibilities" in desc
    assert "Senior Software Engineer (Go)" not in desc
    assert "Back" not in desc.splitlines()[0]
    assert "Apply Now" not in desc
    assert "getElementById" not in desc
