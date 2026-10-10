"""Unit tests for the Manus (careers.manus.im) adapter — custom SPA; no JSON-LD,
no og:site_name, and the page carries no location at all.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_MANUS_URL = "https://careers.manus.im/en/job/664b475a-ca34-46d2-9846-c52f347857e6"


def test_parse_html_manus_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("manus_job.html"), _MANUS_URL)
    assert result["company_name"] == "Manus"
