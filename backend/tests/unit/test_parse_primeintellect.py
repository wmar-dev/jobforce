"""Unit tests for the Prime Intellect (primeintellect.ai) adapter — Next.js careers page with location in a <dl> facts list and the body in an <article> prose block."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_PI_URL = "https://www.primeintellect.ai/careers/fb497090-0336-45b2-b802-9d34d8758d06"


def test_parse_html_primeintellect_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("primeintellect_job.html")
    result = parse_html(html, _PI_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_primeintellect_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("primeintellect_job.html")
    result = parse_html(html, _PI_URL)
    assert result["description"] is not None
    assert "Security is the single highest-stakes function" in result["description"]
