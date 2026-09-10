"""Unit tests for the Factory (factory.com) adapter — Next.js site with a
LOCATION/TYPE/TAGS label-value sidebar inside <article> and a separate
sibling <div> holding the full rich-text job description."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_FACTORY_URL = "https://factory.com/careers/software-engineer-product"


def test_parse_html_factory_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("factory_job.html")
    result = parse_html(html, _FACTORY_URL)
    assert result["location"] == "San Francisco, CA"


def test_parse_html_factory_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("factory_job.html")
    result = parse_html(html, _FACTORY_URL)
    assert result["description"] is not None
    assert "highly capable engineers to own and lead engineering projects" in result["description"]
