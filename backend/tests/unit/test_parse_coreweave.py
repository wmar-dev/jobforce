"""Unit tests for the CoreWeave (coreweave.com) site adapter — scout_fetch
synthesizes this HTML shape from Greenhouse's public Jobs API (see
_fetch_coreweave_greenhouse_html) since the real page hides everything in a
cross-origin iframe.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_COREWEAVE_URL = "https://coreweave.com/careers/job?gh_jid=4663228006&board=coreweave"


def test_parse_html_coreweave_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coreweave_job.html")
    result = parse_html(html, _COREWEAVE_URL)
    assert result["title"] == "Applied AI Engineer, Inference"


def test_parse_html_coreweave_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coreweave_job.html")
    result = parse_html(html, _COREWEAVE_URL)
    assert result["company_name"] == "CoreWeave"


def test_parse_html_coreweave_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coreweave_job.html")
    result = parse_html(html, _COREWEAVE_URL)
    assert result["location"] == "Bellevue, WA/ San Francisco, CA/  Sunnyvale, CA"


def test_parse_html_coreweave_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coreweave_job.html")
    result = parse_html(html, _COREWEAVE_URL)
    assert result["description"] is not None
    assert "Applied AI Engineer" in result["description"]
