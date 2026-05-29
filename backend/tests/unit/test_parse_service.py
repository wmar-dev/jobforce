"""Unit tests for jobforce.services.parse — written test-first (T005/T019/T020)."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# slug_to_location
# ---------------------------------------------------------------------------


def test_slug_to_location_known_city() -> None:
    from jobforce.services.parse import slug_to_location

    assert slug_to_location("/careers/engineer-san-francisco/") == "San Francisco"


def test_slug_to_location_remote() -> None:
    from jobforce.services.parse import slug_to_location

    assert slug_to_location("/jobs/software-engineer-remote") == "Remote"


def test_slug_to_location_unknown_returns_none() -> None:
    from jobforce.services.parse import slug_to_location

    assert slug_to_location("/careers/engineer") is None


# ---------------------------------------------------------------------------
# merge
# ---------------------------------------------------------------------------


def test_merge_override_wins_when_non_null() -> None:
    from jobforce.services.parse import merge

    base = {"title": "Generic Title", "location": None}
    override = {"title": "Specific Title", "location": ""}
    result = merge(base, override)
    assert result["title"] == "Specific Title"
    assert result["location"] is None  # empty string does not override


def test_merge_base_wins_when_override_null() -> None:
    from jobforce.services.parse import merge

    base = {"company_name": "Fallback Co"}
    override = {"company_name": None}
    assert merge(base, override)["company_name"] == "Fallback Co"


# ---------------------------------------------------------------------------
# run_adapter
# ---------------------------------------------------------------------------


def test_run_adapter_catches_field_error() -> None:
    from bs4 import BeautifulSoup

    from jobforce.services.parse import run_adapter

    bad_adapter = {"title": lambda doc, url: 1 / 0}  # will raise ZeroDivisionError
    doc = BeautifulSoup("<html><body></body></html>", "lxml")
    result = run_adapter(bad_adapter, doc, "https://example.com/")
    assert result["title"] is None


def test_run_adapter_returns_values() -> None:
    from bs4 import BeautifulSoup

    from jobforce.services.parse import run_adapter

    adapter = {"title": lambda doc, url: "Hello"}
    doc = BeautifulSoup("<html></html>", "lxml")
    assert run_adapter(adapter, doc, "https://x.com/")["title"] == "Hello"


# ---------------------------------------------------------------------------
# parse_html — generic adapter
# ---------------------------------------------------------------------------


def test_parse_html_generic_extracts_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generic_job.html")
    result = parse_html(html, "https://acme.com/jobs/software-engineer")
    assert result["title"] == "Software Engineer"


def test_parse_html_generic_extracts_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generic_job.html")
    result = parse_html(html, "https://acme.com/jobs/software-engineer")
    assert result["company_name"] == "Acme Corp"


def test_parse_html_generic_extracts_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generic_job.html")
    result = parse_html(html, "https://acme.com/jobs/software-engineer")
    assert result["location"] == "New York, NY"


def test_parse_html_generic_detects_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generic_job.html")
    result = parse_html(html, "https://acme.com/jobs/software-engineer")
    assert result["role_type"] == "full-time"


# ---------------------------------------------------------------------------
# parse_html — OpenAI site adapter
# ---------------------------------------------------------------------------


def test_parse_html_openai_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("openai_job.html")
    result = parse_html(html, "https://openai.com/careers/senior-engineer-san-francisco/")
    assert result["company_name"] == "OpenAI"


def test_parse_html_openai_title_from_main_h2() -> None:
    from jobforce.services.parse import parse_html

    html = _read("openai_job.html")
    result = parse_html(html, "https://openai.com/careers/senior-engineer-san-francisco/")
    assert result["title"] == "Senior Engineer, Robotics"


def test_parse_html_openai_location_from_dom() -> None:
    from jobforce.services.parse import parse_html

    html = _read("openai_job.html")
    result = parse_html(html, "https://openai.com/careers/senior-engineer-san-francisco/")
    assert result["location"] == "Robotics - San Francisco"


def test_parse_html_openai_compensation() -> None:
    from jobforce.services.parse import parse_html

    html = _read("openai_job.html")
    result = parse_html(html, "https://openai.com/careers/senior-engineer-san-francisco/")
    assert result.get("compensation") is not None
    assert "$" in result["compensation"]


def test_parse_html_missing_field_is_null() -> None:
    from jobforce.services.parse import parse_html

    html = "<html><body><h1>Some Job</h1></body></html>"
    result = parse_html(html, "https://unknown-site.com/job/123")
    assert result["location"] is None
    assert result["description"] is None


# ---------------------------------------------------------------------------
# US2: Parity — OpenAI adapter field-for-field match (T019)
# ---------------------------------------------------------------------------


def test_openai_adapter_parity_title() -> None:
    """OpenAI adapter must return title from main h2, not h1."""
    from jobforce.services.parse import parse_html

    html = _read("openai_job.html")
    result = parse_html(html, "https://openai.com/careers/senior-engineer-san-francisco/")
    assert result["title"] == "Senior Engineer, Robotics"
    assert result["company_name"] == "OpenAI"
    assert result["location"] is not None


def test_openai_adapter_overrides_generic_company() -> None:
    """Site adapter company_name must win over generic og:site_name."""
    from jobforce.services.parse import parse_html

    # HTML has no og:site_name so generic would return None; adapter returns "OpenAI"
    html = _read("openai_job.html")
    result = parse_html(html, "https://openai.com/careers/senior-engineer-san-francisco/")
    assert result["company_name"] == "OpenAI"


def test_openai_adapter_slug_fallback_location() -> None:
    """If DOM location paragraph absent, slug_to_location provides fallback."""
    from jobforce.services.parse import parse_html

    html = "<html><body><main><h2>Engineer</h2></main></body></html>"
    result = parse_html(html, "https://openai.com/careers/engineer-san-francisco/")
    assert result["location"] == "San Francisco"


# ---------------------------------------------------------------------------
# US2: Parity — generic adapter produces non-null title and role_type (T020)
# ---------------------------------------------------------------------------


def test_generic_adapter_non_null_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generic_job.html")
    result = parse_html(html, "https://acme.com/jobs/engineer")
    assert result["title"] is not None and result["title"] != ""


def test_generic_adapter_non_null_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("generic_job.html")
    result = parse_html(html, "https://acme.com/jobs/engineer")
    assert result["role_type"] == "full-time"


def test_single_file_adapter_registration() -> None:
    """Adding a new adapter to SITE_ADAPTERS is a one-dict-entry change."""
    from jobforce.services.parse import SITE_ADAPTERS

    # Verify the registry is a plain dict — no framework, no class hierarchy
    assert isinstance(SITE_ADAPTERS, dict)
    assert "openai.com" in SITE_ADAPTERS
    # A new adapter is one line: SITE_ADAPTERS["new-site.com"] = {...}
    SITE_ADAPTERS["test-site.com"] = {"company_name": lambda doc, url: "TestCo"}
    assert "test-site.com" in SITE_ADAPTERS
    del SITE_ADAPTERS["test-site.com"]  # clean up
