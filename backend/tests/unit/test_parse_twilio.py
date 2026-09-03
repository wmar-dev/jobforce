"""Unit tests for the Twilio (jobs.twilio.com) site adapter — Eightfold-powered
ATS on Twilio's own domain. The page's static <h1> always reads "Single
Position" regardless of which job is loaded; the real title lives in an <h2>
further down.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_TWILIO_URL = "https://jobs.twilio.com/careers/job/1099554769400"


def test_parse_html_twilio_title_ignores_static_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["title"] == "Senior Software Engineer"


def test_parse_html_twilio_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["company_name"] == "Twilio"


def test_parse_html_twilio_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["location"] == "Remote - US"


def test_parse_html_twilio_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["description"] is not None
    assert "data infrastructure" in result["description"]
