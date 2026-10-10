"""Unit tests for the Rafay (rafay.co) adapter — Webflow careers pages: the h1 packs
"<title> - <location>" into spans, the description is a .rich-text block.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_RAFAY_URL = "https://rafay.co/careers/inference-optimization-engineer-sr-engineer-sta5-engineer-principal-engineer"


def test_parse_html_rafay_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("rafay_job.html"), _RAFAY_URL)
    assert (
        result["title"]
        == "Inference Optimization Engineer (Sr Engineer / Sta5 Engineer / Principal Engineer)"
    )


def test_parse_html_rafay_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("rafay_job.html"), _RAFAY_URL)
    assert result["company_name"] == "Rafay"


def test_parse_html_rafay_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("rafay_job.html"), _RAFAY_URL)
    assert result["location"] == "India"


def test_parse_html_rafay_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("rafay_job.html"), _RAFAY_URL)
    assert result["description"] is not None
    assert "Model Compression" in result["description"]
    assert "Apply For This Position" not in result["description"]
