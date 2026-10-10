"""Unit tests for the Subconscious (subconscious.dev) adapter — Next.js careers page
with no JobPosting JSON-LD; location rides in a "Department · Location" line.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SUBCONSCIOUS_URL = "https://www.subconscious.dev/careers/platform-engineer-inference"


def test_parse_html_subconscious_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("subconscious_job.html"), _SUBCONSCIOUS_URL)
    assert result["company_name"] == "Subconscious"


def test_parse_html_subconscious_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("subconscious_job.html"), _SUBCONSCIOUS_URL)
    assert result["location"] == "Boston, MA"


def test_parse_html_subconscious_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("subconscious_job.html"), _SUBCONSCIOUS_URL)
    assert result["description"] is not None
    assert "long-running agents" in result["description"]
    assert "Apply now" not in result["description"]
