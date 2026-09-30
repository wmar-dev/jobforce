"""Unit tests for the Gem (jobs.gem.com/<company>/<id>) adapter — company only in URL slug; class names carry numeric suffixes."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"

_GEM_URL = "https://jobs.gem.com/altara/am9icG9zdDrGiWSZkiNcX39c26V88Au8"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_parse_html_gem_title() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("gem_altara_job.html"), _GEM_URL)
    assert result["title"] == "Software Engineer"


def test_parse_html_gem_company_from_url_slug() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("gem_altara_job.html"), _GEM_URL)
    assert result["company_name"] == "Altara"


def test_parse_html_gem_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("gem_altara_job.html"), _GEM_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_gem_description_excludes_apply_form() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("gem_altara_job.html"), _GEM_URL)
    assert result["description"] is not None
    assert "scientific intelligence platform" in result["description"]
    assert "Ready to apply" not in result["description"]
