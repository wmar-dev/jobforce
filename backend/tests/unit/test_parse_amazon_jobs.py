"""Unit tests for the Amazon.jobs (amazon.jobs) adapter — React SPA with a `Location:` label and #job-detail-body sections."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_AMAZON_URL = "https://www.amazon.jobs/en/jobs/10497224/sr-software-engineer-ai-ml-aws-neuron-distributed-training"


def test_parse_html_amazon_jobs_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("amazon_jobs_job.html"), _AMAZON_URL)
    assert result["company_name"] == "Amazon"


def test_parse_html_amazon_jobs_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("amazon_jobs_job.html"), _AMAZON_URL)
    assert result["location"] == "US, CA, San Francisco"


def test_parse_html_amazon_jobs_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("amazon_jobs_job.html"), _AMAZON_URL)
    assert result["description"] is not None
    assert "Annapurna Labs" in result["description"]
    assert "Basic Qualifications" in result["description"]
