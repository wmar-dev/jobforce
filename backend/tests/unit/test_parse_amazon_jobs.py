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


_AMAZON_SIDEBAR_URL = (
    "https://www.amazon.jobs/en/jobs/10373514/applied-scientist-ii-console-science"
)


def test_parse_html_amazon_jobs_sidebar_location() -> None:
    """Newer layout: location sits in the "Job details" sidebar association list."""
    from jobforce.services.parse import parse_html

    result = parse_html(_read("amazon_jobs_sidebar_job.html"), _AMAZON_SIDEBAR_URL)
    assert result["location"] == "USA, CA, Santa Clara"


def test_parse_html_amazon_jobs_role_type_ignores_recommended_jobs() -> None:
    """An intern posting in the "Recommended jobs" widget must not mark this job an internship."""
    from jobforce.services.parse import parse_html

    result = parse_html(_read("amazon_jobs_sidebar_job.html"), _AMAZON_SIDEBAR_URL)
    assert result["role_type"] == "full-time"


def test_parse_html_amazon_jobs_role_type_detects_intern_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("amazon_jobs_sidebar_job.html").replace(
        "Applied Scientist II, Console Science</h1>", "Applied Scientist Intern - 2027</h1>"
    )
    result = parse_html(html, _AMAZON_SIDEBAR_URL)
    assert result["role_type"] == "internship"
