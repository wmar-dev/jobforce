"""Unit tests for the Warner Bros. Discovery (careers.wbd.com, Phenom People ATS)
site adapter.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WBD_URL = "https://careers.wbd.com/global/en/job/R000106532/Staff-Machine-Learning-Engineer-Search"


def test_parse_html_wbd_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["company_name"] == "Warner Bros. Discovery"


def test_parse_html_wbd_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["title"] == "Staff Machine Learning Engineer -  Search"


def test_parse_html_wbd_location_joins_all_and_dedupes() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["location"] == (
        "San Francisco, California, United States of America; "
        "Bellevue, Washington, United States of America"
    )


def test_parse_html_wbd_description_excludes_similar_jobs_and_share_widgets() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["description"] is not None
    assert "Staff Machine Learning Engineer" in result["description"]
    assert "Similar Jobs" not in result["description"]
    assert "Share this opportunity" not in result["description"]
