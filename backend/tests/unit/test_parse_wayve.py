"""Unit tests for the Wayve (wayve.firststage.co) adapter — the generic h1
selector grabs an "Apply for" button, the title, and a run of location/
employment-type/department pill tags all concatenated together with no
separators, producing garbage title/location text. All real fields live in
a JSON-LD <script type="application/ld+json"> JobPosting block instead.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WAYVE_URL = "https://wayve.firststage.co/jobs/0PFdgL07kR/view?layout=grid"


def test_parse_html_wayve_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wayve_job.html")
    result = parse_html(html, _WAYVE_URL)
    assert result["title"] == "Application Software Engineer -  Embedded Software C++"


def test_parse_html_wayve_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wayve_job.html")
    result = parse_html(html, _WAYVE_URL)
    assert result["location"] == "Sunnyvale, California USA, Detroit, Michigan USA"


def test_parse_html_wayve_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wayve_job.html")
    result = parse_html(html, _WAYVE_URL)
    assert result["description"] is not None
    assert "Embodied AI technology" in result["description"]
