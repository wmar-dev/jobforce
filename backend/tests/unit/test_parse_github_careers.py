"""Unit tests for the GitHub (www.github.careers/careers-home/jobs/<id>) site
adapter — a Phenom People/iCIMS board (same "#header-locations" pattern seen on
careers.docusign.com). company_name comes back from the generic adapter as the
full page <title> ("<role> in <location> | GitHub, Inc."), and location isn't
visible via any plain element the generic adapter checks.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_GITHUB_URL = "https://www.github.careers/careers-home/jobs/5679?lang=en-us"


def test_parse_html_github_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("github_job.html")
    result = parse_html(html, _GITHUB_URL)
    assert result["company_name"] == "GitHub"


def test_parse_html_github_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("github_job.html")
    result = parse_html(html, _GITHUB_URL)
    assert result["location"] == "United States"
