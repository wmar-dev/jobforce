"""Unit tests for the Microsoft (apply.careers.microsoft.com) site adapter —
same Eightfold-powered ATS as Twilio's board. The static <h1> always reads
"Single Position" regardless of which job is loaded; the real title lives in
an <h2> further down, and the page never renders the company name as text.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_MICROSOFT_URL = "https://apply.careers.microsoft.com/careers/job/1970393556948193"


def test_parse_html_microsoft_title_ignores_static_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("microsoft_job.html")
    result = parse_html(html, _MICROSOFT_URL)
    assert result["title"] == "Senior Software Engineer"


def test_parse_html_microsoft_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("microsoft_job.html")
    result = parse_html(html, _MICROSOFT_URL)
    assert result["company_name"] == "Microsoft"


def test_parse_html_microsoft_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("microsoft_job.html")
    result = parse_html(html, _MICROSOFT_URL)
    assert result["location"] == "United States, Washington, Redmond"


def test_parse_html_microsoft_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("microsoft_job.html")
    result = parse_html(html, _MICROSOFT_URL)
    assert result["description"] is not None
    assert "advertising stack" in result["description"]
