"""Unit tests for the Surge AI (surgehq.ai) adapter — Webflow CMS site with two
page shapes: templated `/careers?id=...` detail pages (title in h2.js-title,
description in .job-content-richtext.js-desc) and a bespoke `/swe` landing
page with no CMS markup at all, falling back to the generic h1 title and a
<main> description scope.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SURGEHQ_URL = "https://surgehq.ai/careers?id=e5d74eb9-9487-427b-9df7-a9b6c453485d"
_SURGEHQ_SWE_URL = "https://surgehq.ai/swe"


def test_parse_html_surgehq_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_job.html")
    result = parse_html(html, _SURGEHQ_URL)
    assert result["title"] == "Staff Fullstack Engineer"


def test_parse_html_surgehq_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_job.html")
    result = parse_html(html, _SURGEHQ_URL)
    assert result["company_name"] == "Surge AI"


def test_parse_html_surgehq_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_job.html")
    result = parse_html(html, _SURGEHQ_URL)
    assert result["location"] == "Remote"


def test_parse_html_surgehq_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_job.html")
    result = parse_html(html, _SURGEHQ_URL)
    assert result["description"] is not None
    assert "Staff Fullstack Engineer at Surge" in result["description"]


def test_parse_html_surgehq_swe_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_swe_job.html")
    result = parse_html(html, _SURGEHQ_SWE_URL)
    assert result["title"] == "Senior Software Engineer: Agentic Coding RL Environments"


def test_parse_html_surgehq_swe_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_swe_job.html")
    result = parse_html(html, _SURGEHQ_SWE_URL)
    assert result["company_name"] == "Surge AI"


def test_parse_html_surgehq_swe_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("surgehq_swe_job.html")
    result = parse_html(html, _SURGEHQ_SWE_URL)
    assert result["description"] is not None
    assert "Coding agents are strong today" in result["description"]
    assert "Surge AI" not in result["description"]
