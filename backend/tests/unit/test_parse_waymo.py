"""Unit tests for the Waymo (careers.withwaymo.com/jobs/<slug>) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WAYMO_URL = "https://careers.withwaymo.com/jobs/machine-learning-engineer-perception-llm-vlm"


def test_parse_html_waymo_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("waymo_job.html")
    result = parse_html(html, _WAYMO_URL)
    assert result["company_name"] == "Waymo"


def test_parse_html_waymo_title_ignores_sitewide_headings() -> None:
    from jobforce.services.parse import parse_html

    html = _read("waymo_job.html")
    result = parse_html(html, _WAYMO_URL)
    assert result["title"] == "Machine Learning Engineer Perception LLM/VLM (PhD, New Grad)"


def test_parse_html_waymo_location_ignores_related_jobs_sidebar() -> None:
    from jobforce.services.parse import parse_html

    html = _read("waymo_job.html")
    result = parse_html(html, _WAYMO_URL)
    assert result["location"] == "Mountain View, California, San Francisco, California"
