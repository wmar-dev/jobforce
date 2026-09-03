"""Unit tests for the Grid Dynamics (griddynamics.com/careers/vacancy/<id>) site
adapter — title extracts fine via the generic adapter, but location isn't
visible via any plain element the generic adapter checks, and the generic
adapter's description falls back to the short meta description rather than the
full vacancy body.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_GRIDDYNAMICS_URL = "https://www.griddynamics.com/careers/vacancy/59817"


def test_parse_html_griddynamics_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("griddynamics_job.html")
    result = parse_html(html, _GRIDDYNAMICS_URL)
    assert result["location"] == "US Remote, US"


def test_parse_html_griddynamics_description_prefers_full_body_over_meta() -> None:
    """The generic adapter falls back to the short <meta name="description">
    tag, which drops the "Essential functions" list present in the full
    vacancy body."""
    from jobforce.services.parse import parse_html

    html = _read("griddynamics_job.html")
    result = parse_html(html, _GRIDDYNAMICS_URL)
    assert result["description"] is not None
    assert "Essential functions" in result["description"]
