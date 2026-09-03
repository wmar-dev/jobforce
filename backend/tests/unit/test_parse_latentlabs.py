"""Unit tests for the Latent Labs (latentlabs.com) adapter — WordPress job
template; title/company already extract via the generic adapter, but location
lives in a `.tag_list span.tag` next to the h1 and description lives across
several `.box_width > .right_desc` sections with no "description" class hook.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_LATENTLABS_URL = "https://www.latentlabs.com/job/member-of-technical-staff-applied-ai/"


def test_parse_html_latentlabs_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("latentlabs_job.html")
    result = parse_html(html, _LATENTLABS_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_latentlabs_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("latentlabs_job.html")
    result = parse_html(html, _LATENTLABS_URL)
    assert result["description"] is not None
    assert "deep expertise in generative modelling" in result["description"]
