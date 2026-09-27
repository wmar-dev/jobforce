"""Unit tests for the Moss (moss.dev) adapter — the job page carries a clean
schema.org JobPosting JSON-LD block for structured fields (location), but its
own `description` field is a one-line summary, so the full body comes from
the #job-panel-overview tabpanel instead.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_MOSS_URL = "https://www.moss.dev/careers/founding-ml-engineer"


def test_parse_html_moss_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("moss_job.html")
    result = parse_html(html, _MOSS_URL)
    assert result["location"] == "San Francisco, CA / Remote"


def test_parse_html_moss_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("moss_job.html")
    result = parse_html(html, _MOSS_URL)
    assert result["description"] is not None
    assert "Train and fine-tune embedding and reranking models" in result["description"]
