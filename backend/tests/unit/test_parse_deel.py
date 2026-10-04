"""Unit tests for the Deel ATS (jobs.deel.com) site adapter — Next.js/MUI page
with no <h1> element and a multi-tenant URL (/<company-slug>/job-details/...);
title, company, and location come from the schema.org JobPosting JSON-LD block,
description from the RichTextDisplay container.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_DEEL_URL = (
    "https://jobs.deel.com/swingvision/job-details/c2cc0f23-3e59-4c03-849e-d53e7567a3fd/overview"
)


def test_parse_html_deel_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("deel_job.html"), _DEEL_URL)
    assert result["title"] == "Head of Machine Learning"


def test_parse_html_deel_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("deel_job.html"), _DEEL_URL)
    assert result["company_name"] == "SwingVision, Inc."


def test_parse_html_deel_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("deel_job.html"), _DEEL_URL)
    assert result["location"] == "Berkeley - CA"


def test_parse_html_deel_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("deel_job.html"), _DEEL_URL)
    assert result["description"] is not None
    assert "Own the Technical Roadmap" in result["description"]
    assert "Job details" not in result["description"]
