"""Framework-level unit tests for jobforce.services.parse — written test-first
(T005/T019/T020).

Site-specific adapter tests live in their own ``test_parse_<site>.py`` files
alongside this one; only framework and generic-adapter behaviour belongs here.
"""

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


def test_parse_html_missing_field_is_null() -> None:
    from jobforce.services.parse import parse_html

    html = "<html><body><h1>Some Job</h1></body></html>"
    result = parse_html(html, "https://unknown-site.com/job/123")
    assert result["location"] is None
    assert result["description"] is None


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


# ---------------------------------------------------------------------------
# _match_adapter — suffix matching
# ---------------------------------------------------------------------------


def test_match_adapter_exact_match() -> None:
    from jobforce.services.parse import SITE_ADAPTERS, _match_adapter

    assert _match_adapter("openai.com") is SITE_ADAPTERS["openai.com"]


def test_match_adapter_no_match_returns_empty() -> None:
    from jobforce.services.parse import _match_adapter

    assert _match_adapter("unknown-ats.io") == {}


def test_match_adapter_www_prefix_stripped_by_caller() -> None:
    from jobforce.services.parse import SITE_ADAPTERS, _match_adapter

    # parse_html strips www. before calling _match_adapter
    assert _match_adapter("boards.greenhouse.io") is SITE_ADAPTERS["boards.greenhouse.io"]
