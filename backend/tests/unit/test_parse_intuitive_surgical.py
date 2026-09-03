"""Unit tests for the Intuitive Surgical
(careers.intuitive.com/en/jobs/<id>/<req>/<slug>/) site adapter — title extracts
fine via the generic adapter's <h1> selector, but company_name comes back as
the og:site_name meta ("Intuitive Surgical Careers" instead of "Intuitive
Surgical"), and location/description aren't exposed via any plain element the
generic adapter checks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_INTUITIVE_URL = (
    "https://careers.intuitive.com/en/jobs/744000138714310/JOB215151/sr-mobile-app-developer/"
)


def test_parse_html_intuitivesurgical_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("intuitivesurgical_job.html")
    result = parse_html(html, _INTUITIVE_URL)
    assert result["company_name"] == "Intuitive Surgical"


def test_parse_html_intuitivesurgical_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("intuitivesurgical_job.html")
    result = parse_html(html, _INTUITIVE_URL)
    assert result["location"] == "Sunnyvale, CA, United States"


def test_parse_html_intuitivesurgical_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("intuitivesurgical_job.html")
    result = parse_html(html, _INTUITIVE_URL)
    assert result["description"] is not None
    assert "react native and native android" in result["description"]
