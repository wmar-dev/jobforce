"""Unit tests for the Middleware (middleware.io) adapter — WordPress-style careers
page: h1 split across spans, "Location:" paragraph in .job-details, no JSON-LD job data.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_MIDDLEWARE_URL = "https://middleware.io/careers/senior-backend-software-engineer/"


def test_parse_html_middleware_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("middleware_job.html"), _MIDDLEWARE_URL)
    assert result["title"] == "Senior Software Engineer (Backend)"


def test_parse_html_middleware_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("middleware_job.html"), _MIDDLEWARE_URL)
    assert result["company_name"] == "Middleware"


def test_parse_html_middleware_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("middleware_job.html"), _MIDDLEWARE_URL)
    assert result["location"] == "Ahmedabad"
