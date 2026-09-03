"""Unit tests for the Asana (asana.com/jobs/apply/<id>) site adapter — title
parses fine via the generic adapter's <h1> selector, but company_name falls
back to the wrong og:site_name ("Asana Jobs") and location/description need
dedicated selectors since they're not tagged with any location/description
class.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ASANA_URL = "https://asana.com/jobs/apply/8084470"


def test_parse_html_asana_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["title"] == "Senior Software Engineer, Infrastructure Security"


def test_parse_html_asana_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["company_name"] == "Asana"


def test_parse_html_asana_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_asana_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["description"] is not None
    assert "Security Development team" in result["description"]
