"""Unit tests for the Polymer-hosted careers adapter (careers.honeyhive.ai/<id>)."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"

_POLYMER_URL = "https://careers.honeyhive.ai/38256"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_polymer_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("polymer_honeyhive_job.html"), _POLYMER_URL)
    assert result["title"] == "Member of Technical Staff, Platform"


def test_parse_html_polymer_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("polymer_honeyhive_job.html"), _POLYMER_URL)
    assert result["company_name"] == "HoneyHive"


def test_parse_html_polymer_location_skips_department_and_type() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("polymer_honeyhive_job.html"), _POLYMER_URL)
    assert result["location"] == "New York or San Francisco"


def test_parse_html_polymer_description() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("polymer_honeyhive_job.html"), _POLYMER_URL)
    assert result["description"] is not None
    assert "observability stack for AI agents" in result["description"]
