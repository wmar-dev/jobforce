"""Unit tests for the iCIMS (*.icims.com) adapter. The real job content only
ever exists inside a same-origin iframe scout_fetch.py merges into the
top-level wrapper's <head> before parse_html ever sees it (see
`_extract_icims_frame_html`) — title and company_name already resolve via the
generic adapter once that merge happens, so this adapter only overrides
location and description."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ICIMS_URL = "https://careers-here.icims.com/jobs/83538/partner-account-manager/job"


def test_parse_html_icims_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("icims_job.html")
    result = parse_html(html, _ICIMS_URL)
    assert result["location"] == "FR-Courbevoie"


def test_parse_html_icims_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("icims_job.html")
    result = parse_html(html, _ICIMS_URL)
    assert result["description"] is not None
    assert "Solution Partners" in result["description"]
