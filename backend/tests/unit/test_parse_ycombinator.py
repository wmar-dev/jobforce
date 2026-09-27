"""Unit tests for the Y Combinator jobs board (ycombinator.com/companies/<slug>/jobs/<id>)
adapter — a multi-tenant board like Ashby/Greenhouse hosting many YC
companies' postings, so company_name must come from the posting's own
h2.text-2xl rather than a generic og:site_name (which is just "Y Combinator"
site-wide); location is one of several bullet-separated spans next to the
title with no dedicated class.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_YC_URL = "https://www.ycombinator.com/companies/tamarind-bio/jobs/HPRZAz3-infrastructure-engineer"


def test_parse_html_ycombinator_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ycombinator_job.html")
    result = parse_html(html, _YC_URL)
    assert result["company_name"] == "Tamarind Bio"


def test_parse_html_ycombinator_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ycombinator_job.html")
    result = parse_html(html, _YC_URL)
    assert result["location"] == "San Francisco, CA, US"


def test_parse_html_ycombinator_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ycombinator_job.html")
    result = parse_html(html, _YC_URL)
    assert result["description"] is not None
    assert "scaling of our machine learning inference system" in result["description"]
