"""Unit tests for the Bowser AI (bowserai.com) adapter — static job pages with a
.header block (.company, h1, .meta) followed by .section blocks of description.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_URL = "https://bowserai.com/jobs/ea934834-1e93-417f-a547-d3186aaee711/"


def test_parse_html_bowserai_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("bowserai_job.html"), _URL)
    assert result["company_name"] == "Bowser AI"


def test_parse_html_bowserai_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("bowserai_job.html"), _URL)
    assert result["location"] == "Remote (Pacific Time preferred)"


def test_parse_html_bowserai_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("bowserai_job.html"), _URL)
    assert result["description"] is not None
    assert "voice agents" in result["description"]
