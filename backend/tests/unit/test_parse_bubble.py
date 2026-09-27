"""Unit tests for the Bubble (bubble.io) site adapter — dogfooded on Bubble
itself, so the job page has no stable class hooks; location lives in a
paragraph following a "Location:" label instead of a dedicated element.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BUBBLE_URL = "https://bubble.io/job?jid=32a3ade2-1e62-4ad9-9ab8-32036d6f7b6b"


def test_parse_html_bubble_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("bubble_job.html")
    result = parse_html(html, _BUBBLE_URL)
    assert result["location"] == (
        "This is a remote-friendly role open to candidates authorized to work "
        "in the U.S. Our team is based in NYC and works Eastern Time."
    )


def test_parse_html_bubble_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("bubble_job.html")
    result = parse_html(html, _BUBBLE_URL)
    assert result["description"] is not None
    assert "next-generation AI-powered development workflows" in result["description"]


def test_parse_html_bubble_location_inline_with_label() -> None:
    """Some job pages put the label and sentence in the same <p> instead of
    splitting them across two consecutive <p> tags (see bubble_job.html)."""
    from jobforce.services.parse import parse_html

    html = _read("bubble_job_inline_location.html")
    result = parse_html(html, _BUBBLE_URL)
    assert result["location"] == (
        "This is a remote-friendly role open to candidates authorized to work "
        "in the U.S. Our team is based in NYC and works Eastern Time."
    )


def test_parse_html_bubble_location_trailing_label() -> None:
    """Other job pages tack the label onto the end of an unrelated (e.g.
    compensation) paragraph, with the actual sentence in the next <p>."""
    from jobforce.services.parse import parse_html

    html = _read("bubble_job_trailing_label.html")
    result = parse_html(html, _BUBBLE_URL)
    assert result["location"] == (
        "This is a remote-friendly role open to candidates authorized to work "
        "in the U.S. Our team is based in NYC and works Eastern Time."
    )
