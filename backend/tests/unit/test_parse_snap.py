"""Unit tests for the Snap Inc (careers.snap.com) adapter — custom design
system site with no og:site_name/footer to derive company_name from, and two
elements sharing the same data-testid where the larger one is the actual
description.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SNAP_URL = "https://careers.snap.com/job?id=R0046616"


def test_parse_html_snap_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("snap_job.html")
    result = parse_html(html, _SNAP_URL)
    assert result["title"] == "Machine Learning Engineer, Causal Inference, Level 5"


def test_parse_html_snap_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("snap_job.html")
    result = parse_html(html, _SNAP_URL)
    assert result["company_name"] == "Snap Inc."


def test_parse_html_snap_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("snap_job.html")
    result = parse_html(html, _SNAP_URL)
    assert result["location"] == "Bellevue; Los Angeles; New York; Palo Alto; Seattle"


def test_parse_html_snap_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("snap_job.html")
    result = parse_html(html, _SNAP_URL)
    assert result["description"] is not None
    assert "Causal Inference team" in result["description"]
