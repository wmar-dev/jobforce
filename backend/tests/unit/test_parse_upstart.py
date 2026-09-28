"""Unit tests for the Upstart (careers.upstart.com) site adapter — a custom
Phenom-style careers page. Company name has no on-page element (single-tenant
site, so it's fixed), and location lives in a "Position location" label
followed by inline text rather than a dedicated element.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_UPSTART_URL = (
    "https://careers.upstart.com/jobs/"
    "senior-software-engineer-upstart-bank-1fdb37db-83d2-4062-a3d7-4ffa1c1aa72d"
)


def test_parse_html_upstart_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("upstart_job.html")
    result = parse_html(html, _UPSTART_URL)
    assert result["company_name"] == "Upstart"


def test_parse_html_upstart_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("upstart_job.html")
    result = parse_html(html, _UPSTART_URL)
    assert result["location"] == "Remote"


def test_parse_html_upstart_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("upstart_job.html")
    result = parse_html(html, _UPSTART_URL)
    assert result["description"] is not None
    assert "radically reduce the cost and complexity of borrowing" in result["description"]


def test_parse_html_upstart_heading_location() -> None:
    """Some postings use a "Position Location" <h2> heading followed by a
    sibling <p> of prose ("This role is available remotely...") instead of
    the inline <strong> label."""
    from jobforce.services.parse import parse_html

    html = _read("upstart_heading_location_job.html")
    result = parse_html(html, _UPSTART_URL)
    assert result["location"] == "Remote"


def test_parse_html_upstart_bare_location() -> None:
    """Some postings state the location as a bare value right after the
    label ("Position location Remote") with no "in the following
    locations:" phrasing."""
    from jobforce.services.parse import parse_html

    html = _read("upstart_bare_location_job.html")
    result = parse_html(html, _UPSTART_URL)
    assert result["location"] == "Remote"


def test_parse_html_upstart_dash_label_location() -> None:
    """Some postings render the label as <strong><em>Position Location
    -&nbsp;</em></strong> (trailing dash, nested em) rather than a plain
    <strong>Position location</strong>."""
    from jobforce.services.parse import parse_html

    html = _read("upstart_dash_label_location_job.html")
    result = parse_html(html, _UPSTART_URL)
    assert result["location"] == "Remote, San Mateo, Columbus, Austin"
