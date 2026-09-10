"""Unit tests for the Renaissance Philanthropy (renaissancephilanthropy.org)
adapter — Squarespace site with no <h1>. Job title lives in the first
h2.preFade text block (sometimes suffixed "at Renaissance Philanthropy"),
the location/comp blurb is the <p> immediately before the "About Renaissance
Philanthropy" <h3>, and the full posting content lives in <main id="page">."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_RP_URL = "https://www.renaissancephilanthropy.org/careers/research-engineer-engineering-hub"


def test_parse_html_renaissancephilanthropy_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("renaissancephilanthropy_job.html")
    result = parse_html(html, _RP_URL)
    assert result["title"] == "Research Engineer, Engineering Hub"


def test_parse_html_renaissancephilanthropy_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("renaissancephilanthropy_job.html")
    result = parse_html(html, _RP_URL)
    assert result["company_name"] == "Renaissance Philanthropy"


def test_parse_html_renaissancephilanthropy_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("renaissancephilanthropy_job.html")
    result = parse_html(html, _RP_URL)
    assert result["location"] == "Remote"


def test_parse_html_renaissancephilanthropy_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("renaissancephilanthropy_job.html")
    result = parse_html(html, _RP_URL)
    assert result["description"] is not None
    assert "on-demand development technical assistance" in result["description"]
