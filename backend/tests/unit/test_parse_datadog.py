"""Unit tests for the Datadog careers site (careers.datadoghq.com) adapter.

The page is a client-rendered React app: title lives in an `<h2>` (the
generic adapter only checks `h1`, so it falls back to the `<title>` tag and
gets truncated at the first "-"), location is a plain unclassed `<p>` right
after the title (no ".location"/"[data-location]" match), and og:site_name
is "Datadog Careers | Datadog" rather than a clean company name.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_DATADOG_URL = "https://careers.datadoghq.com/detail/8094106/?gh_jid=8094106"


def test_parse_html_datadog_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("datadog_job.html")
    result = parse_html(html, _DATADOG_URL)
    assert result["title"] == "Staff Software Engineer - Corporate Development"


def test_parse_html_datadog_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("datadog_job.html")
    result = parse_html(html, _DATADOG_URL)
    assert result["location"] == "San Francisco, California, USA"


def test_parse_html_datadog_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("datadog_job.html")
    result = parse_html(html, _DATADOG_URL)
    assert result["company_name"] == "Datadog"
