"""Unit tests for the CareerPuck (app.careerpuck.com) adapter — multi-tenant
Greenhouse front-end; company name comes from the logo alt text, location from
a styled-component div (description parses via the generic adapter).
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_URL = "https://app.careerpuck.com/job-board/lyft/job/8806570002?gh_jid=8806570002"


def test_parse_html_careerpuck_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("careerpuck_lyft_job.html"), _URL)
    assert result["company_name"] == "Lyft"


def test_parse_html_careerpuck_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("careerpuck_lyft_job.html"), _URL)
    assert result["location"] == "San Francisco, CA"
