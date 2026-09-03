"""Unit tests for the Brex (brex.com/careers/<id>) site adapter — title and
company_name already extract correctly via the generic adapter; location is a
bare <h4>, and the description sits in the parent of Greenhouse's
".content-intro" wrapper div (this page renders Greenhouse's job content HTML
directly).
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BREX_URL = "https://www.brex.com/careers/8606890002"


def test_parse_html_brex_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brex_job.html")
    result = parse_html(html, _BREX_URL)
    assert result["title"] == "AI Engineer, Ecosystem"


def test_parse_html_brex_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brex_job.html")
    result = parse_html(html, _BREX_URL)
    assert result["location"] == "San Francisco, California, United States"


def test_parse_html_brex_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brex_job.html")
    result = parse_html(html, _BREX_URL)
    assert result["description"] is not None
    assert "agentic integrations" in result["description"]
