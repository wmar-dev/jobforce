"""Unit tests for the GenHealth.ai (genhealth.ai) site adapter — custom Next.js
careers page; no company name or JobPosting JSON-LD, description lives in an
``article.cmscontent`` block.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_GENHEALTH_URL = "https://genhealth.ai/jobs/full-stack-eng"


def test_parse_html_genhealth_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("genhealth_job.html"), _GENHEALTH_URL)
    assert result["title"] == "Full Stack Senior/Principal Engineer"


def test_parse_html_genhealth_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("genhealth_job.html"), _GENHEALTH_URL)
    assert result["company_name"] == "GenHealth.ai"


def test_parse_html_genhealth_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("genhealth_job.html"), _GENHEALTH_URL)
    assert result["description"] is not None
    assert "RESTful APIs" in result["description"]
    assert "Apply for" not in result["description"]
