"""Unit tests for the SentinelOne (sentinelone.com) site adapter — scout_fetch
synthesizes this HTML shape from Greenhouse's public Jobs API (see
_fetch_sentinelone_greenhouse_html) since the real page hides everything in a
cross-origin iframe (board token "sentinellabs").
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SENTINELONE_URL = "https://www.sentinelone.com/jobs/?gh_jid=7551201003"


def test_parse_html_sentinelone_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sentinelone_job.html")
    result = parse_html(html, _SENTINELONE_URL)
    assert result["title"] == "Principal AI Engineering Architect"


def test_parse_html_sentinelone_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sentinelone_job.html")
    result = parse_html(html, _SENTINELONE_URL)
    assert result["company_name"] == "SentinelOne"


def test_parse_html_sentinelone_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sentinelone_job.html")
    result = parse_html(html, _SENTINELONE_URL)
    assert result["location"] == "United States - Remote"


def test_parse_html_sentinelone_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sentinelone_job.html")
    result = parse_html(html, _SENTINELONE_URL)
    assert result["description"] is not None
    assert "agentic AI platform" in result["description"]
