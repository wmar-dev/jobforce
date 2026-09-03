"""Unit tests for the Nebius (careers.nebius.com) site adapter — scout_fetch
synthesizes this HTML shape from Greenhouse's public Jobs API (see
_fetch_nebius_greenhouse_html) since the real page hides everything in a
cross-origin iframe.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_NEBIUS_URL = "https://careers.nebius.com/?gh_jid=4765610101"


def test_parse_html_nebius_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["title"] == "Infrastructure Software Engineer"


def test_parse_html_nebius_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["company_name"] == "Nebius"


def test_parse_html_nebius_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["location"] == "Remote - United States"


def test_parse_html_nebius_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["description"] is not None
    assert "bare-metal infrastructure" in result["description"]
