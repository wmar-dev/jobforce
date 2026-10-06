"""Unit tests for the Artificial Analysis (artificialanalysis.ai) site adapter —
Next.js careers page; company name, location, and description live in custom
markup with no generic-adapter hooks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_AA_URL = "https://artificialanalysis.ai/careers/member-of-technical-staff"


def test_parse_html_artificialanalysis_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("artificialanalysis_job.html"), _AA_URL)
    assert result["company_name"] == "Artificial Analysis"


def test_parse_html_artificialanalysis_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("artificialanalysis_job.html"), _AA_URL)
    assert result["location"] == "San Francisco (On-site)"


def test_parse_html_artificialanalysis_description() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("artificialanalysis_job.html"), _AA_URL)
    assert result["description"] is not None
    assert "Design evaluations that set the standard" in result["description"]
    assert "Apply now" not in result["description"]
