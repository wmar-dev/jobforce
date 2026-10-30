"""Unit tests for the White Circle (whitecircle.com) adapter — Next.js/Tailwind
careers page; a ``header#job-overview`` card holds chip spans (location first,
then workplace/team), the h1 title, and a summary paragraph, followed by an
``article.job-description`` body.
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_WHITECIRCLE_URL = (
    "https://whitecircle.com/careers/design-engineer-d5151e8d-e608-4ad0-a56a-845a094b49b0"
)
_WHITECIRCLE_ML_URL = (
    "https://whitecircle.com/careers/ml-research-engineer-49c8b015-2d99-4173-b9a7-b4a0a0316eff"
)

_CASES = [
    ("whitecircle_job.html", _WHITECIRCLE_URL, "Design Engineer", "NY, SF, LA"),
    ("whitecircle_ml_job.html", _WHITECIRCLE_ML_URL, "ML Research Engineer", "Paris, London"),
]


@pytest.mark.parametrize(("fixture", "url", "title", "location"), _CASES)
def test_parse_html_whitecircle_company(fixture: str, url: str, title: str, location: str) -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read(fixture), url)
    assert result["company_name"] == "White Circle"


@pytest.mark.parametrize(("fixture", "url", "title", "location"), _CASES)
def test_parse_html_whitecircle_location(fixture: str, url: str, title: str, location: str) -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read(fixture), url)
    assert result["location"] == location


def test_parse_html_whitecircle_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("whitecircle_job.html"), _WHITECIRCLE_URL)
    assert result["description"] is not None
    assert "turn complex AI safety workflows into simple" in result["description"]
    assert "About White Circle" in result["description"]
