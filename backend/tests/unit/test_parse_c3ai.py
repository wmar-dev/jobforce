"""Unit tests for the C3.ai (c3.ai) site adapter — Next.js job page. Title is a
bare <h1>, location/department share one <p> right after it ("City, ST ·
Department"), and the full JD (intro, responsibilities, pay range, EEO
conclusion) lives in the wrapper <div> that follows the "Apply Now" button.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_C3AI_URL = "https://c3.ai/job-description?gh_jid=6225305002"


def test_parse_html_c3ai_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("c3ai_job.html")
    result = parse_html(html, _C3AI_URL)
    assert result["company_name"] == "C3 AI"


def test_parse_html_c3ai_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("c3ai_job.html")
    result = parse_html(html, _C3AI_URL)
    assert result["location"] == "Redwood City, CA"


def test_parse_html_c3ai_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("c3ai_job.html")
    result = parse_html(html, _C3AI_URL)
    assert result["description"] is not None
    assert "AI Studio team" in result["description"]
    assert "Equal Opportunity" in result["description"]
