"""Unit tests for the Coinbase (coinbase.com/careers/positions/<id>) site
adapter — title extracts fine via the generic adapter's <h1>. Location is the
first of two <span> tags in the div right after the <h1> (location, then Job
ID); Coinbase renders Greenhouse's job content HTML directly, including its
".content-intro" wrapper div, so the description container is that div's parent
— same pattern as Brex.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_COINBASE_URL = "https://www.coinbase.com/careers/positions/7739592"


def test_parse_html_coinbase_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["title"] == "Senior Machine Learning Engineer"


def test_parse_html_coinbase_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["company_name"] == "Coinbase"


def test_parse_html_coinbase_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["location"] == "Remote - USA"


def test_parse_html_coinbase_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["description"] is not None
    assert "models that power Coinbase's core products" in result["description"]
