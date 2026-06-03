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


def test_openai_adapter_real_layout_location_from_dom() -> None:
    """Real OpenAI page layout: location p is next sibling of title h2, not after About the Team h2."""
    from jobforce.services.parse import parse_html

    html = _read("openai_job_real_layout.html")
    result = parse_html(
        html,
        "https://openai.com/careers/software-engineer-monetization-product-and-platform-san-francisco/",
    )
    assert result["location"] == "Applied AI Engineering - San Francisco and Seattle"


def test_openai_adapter_real_layout_does_not_grab_team_description() -> None:
    """Regression: old main h2 ~ p selector grabbed team description paragraph instead of location."""
    from jobforce.services.parse import parse_html

    html = _read("openai_job_real_layout.html")
    result = parse_html(
        html,
        "https://openai.com/careers/software-engineer-monetization-product-and-platform-san-francisco/",
    )
    assert "cross-functional group" not in (result["location"] or "")


def test_openai_adapter_real_layout_compensation() -> None:
    from jobforce.services.parse import parse_html

    html = _read("openai_job_real_layout.html")
    result = parse_html(
        html,
        "https://openai.com/careers/software-engineer-monetization-product-and-platform-san-francisco/",
    )
    assert result.get("compensation") == "$230K – $385K + Offers Equity"


def test_openai_team_desc_layout_falls_back_to_slug() -> None:
    """Regression: first <p> after title h2 is a team description, not a location — must fall back to slug."""
    from jobforce.services.parse import parse_html

    html = _read("openai_job_team_desc_layout.html")
    result = parse_html(
        html, "https://openai.com/careers/software-engineer-accelerators-san-francisco/"
    )
    assert result["location"] == "San Francisco"


def test_openai_team_desc_layout_does_not_use_team_desc_as_location() -> None:
    """Team description paragraph must not be stored as the location."""
    from jobforce.services.parse import parse_html

    html = _read("openai_job_team_desc_layout.html")
    result = parse_html(
        html, "https://openai.com/careers/software-engineer-accelerators-san-francisco/"
    )
    assert "Kernels team" not in (result["location"] or "")


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
# parse_html — Greenhouse adapter (boards.greenhouse.io)
# ---------------------------------------------------------------------------


def test_parse_html_greenhouse_company_from_url_path() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["company_name"] == "Stripe"


def test_parse_html_greenhouse_location_from_dom() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["location"] == "San Francisco, CA"


def test_parse_html_greenhouse_title_from_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["title"] == "Staff Engineer"


def test_parse_html_greenhouse_job_boards_subdomain() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/stripe/jobs/12345")
    assert result["company_name"] == "Stripe"


def test_parse_html_greenhouse_detects_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["role_type"] == "full-time"


# ---------------------------------------------------------------------------
# parse_html — Workday adapter (*.myworkdayjobs.com)
# ---------------------------------------------------------------------------


def test_parse_html_workday_title_from_automation_id() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["title"] == "Senior Software Engineer"


def test_parse_html_workday_location_from_automation_id() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["location"] == "Austin, TX"


def test_parse_html_workday_company_from_subdomain() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["company_name"] == "Acme"


def test_parse_html_workday_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job.html")
    result = parse_html(
        html,
        "https://acme.wd1.myworkdayjobs.com/en-US/Careers/job/Austin/Senior-Software-Engineer_JR-001",
    )
    assert result["description"] is not None
    assert "platform" in result["description"].lower()


def test_parse_html_workday_suffix_match_applies_adapter() -> None:
    from jobforce.services.parse import SITE_ADAPTERS, _match_adapter

    assert "myworkdayjobs.com" in SITE_ADAPTERS
    assert _match_adapter("acme.wd1.myworkdayjobs.com") is SITE_ADAPTERS["myworkdayjobs.com"]


# ---------------------------------------------------------------------------
# parse_html — Ashby adapter (jobs.ashbyhq.com)
# ---------------------------------------------------------------------------


def test_parse_html_ashby_title_from_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["title"] == "Principal Engineer"


def test_parse_html_ashby_company_from_url_path() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["company_name"] == "Figma"


def test_parse_html_ashby_location_from_brief_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["location"] == "New York, NY"


def test_parse_html_ashby_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["description"] is not None
    assert "design" in result["description"].lower()


def test_parse_html_ashby_hyphenated_company_capitalized() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/linear-app/xyz-456")
    assert result["company_name"] == "Linear App"


# ---------------------------------------------------------------------------
# parse_html — Ashby new markup (ashby_decagon_job.html)
# Fixture captured from jobs.ashbyhq.com/decagon when location was returning
# None due to Ashby renaming .ashby-job-posting-brief-description-item to
# a left-pane labeled-section layout (<h2>Location</h2><p>…</p>).
# ---------------------------------------------------------------------------


def test_parse_html_ashby_new_markup_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["title"] == "Senior Software Engineer, Agent Orchestration"


def test_parse_html_ashby_new_markup_company_from_url() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["company_name"] == "Decagon"


def test_parse_html_ashby_new_markup_location_from_labeled_section() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["location"] == "San Francisco"


def test_parse_html_ashby_new_markup_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("ashby_decagon_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/decagon/75f544ae")
    assert result["description"] is not None
    assert "orchestration" in result["description"].lower()


def test_parse_html_ashby_old_markup_location_still_works() -> None:
    """Fallback to legacy .ashby-job-posting-brief-description-item still works."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/figma/abc-123")
    assert result["location"] == "New York, NY"


# ---------------------------------------------------------------------------
# parse_html — Anthropic via job-boards.greenhouse.io
# ---------------------------------------------------------------------------


def test_parse_html_anthropic_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["title"] == "Research Engineer, Interpretability"


def test_parse_html_anthropic_company_from_url_path() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["company_name"] == "Anthropic"


def test_parse_html_anthropic_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["location"] == "San Francisco, CA"


def test_parse_html_anthropic_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["description"] is not None
    assert "interpretability" in result["description"].lower()


def test_parse_html_anthropic_role_type_none_for_vevraa_boilerplate() -> None:
    # "government contractor" in VEVRAA boilerplate must not match — word boundary
    # check on \bcontract\b excludes "contractor".
    from jobforce.services.parse import parse_html

    html = _read("anthropic_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/anthropic/jobs/4980430008")
    assert result["role_type"] is None


# ---------------------------------------------------------------------------
# parse_html — Databricks adapter (databricks.com)
# ---------------------------------------------------------------------------


def test_parse_html_databricks_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["title"] == "Senior Software Engineer - Backend"


def test_parse_html_databricks_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["company_name"] == "Databricks"


def test_parse_html_databricks_location_strips_apply_button() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["location"] == "San Francisco, CA"


def test_parse_html_databricks_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["description"] is not None
    assert "distributed" in result["description"].lower()


def test_parse_html_databricks_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("databricks_job.html")
    result = parse_html(
        html,
        "https://www.databricks.com/company/careers/engineering/senior-software-engineer---backend-8320183002",
    )
    assert result["role_type"] == "full-time"


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


# ---------------------------------------------------------------------------
# CLI — _validate_url
# ---------------------------------------------------------------------------


def test_validate_url_accepts_https() -> None:
    from jobforce.cli.scout_fetch import _validate_url

    assert (
        _validate_url("https://jobs.example.com/posting/123")
        == "https://jobs.example.com/posting/123"
    )


def test_validate_url_accepts_http() -> None:
    from jobforce.cli.scout_fetch import _validate_url

    assert (
        _validate_url("http://jobs.example.com/posting/123")
        == "http://jobs.example.com/posting/123"
    )


def test_validate_url_rejects_no_scheme() -> None:
    import argparse

    import pytest

    from jobforce.cli.scout_fetch import _validate_url

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_url("jobs.example.com/posting/123")


def test_validate_url_rejects_ftp_scheme() -> None:
    import argparse

    import pytest

    from jobforce.cli.scout_fetch import _validate_url

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_url("ftp://jobs.example.com/posting/123")


def test_validate_url_rejects_empty_netloc() -> None:
    import argparse

    import pytest

    from jobforce.cli.scout_fetch import _validate_url

    with pytest.raises(argparse.ArgumentTypeError):
        _validate_url("https://")


# ---------------------------------------------------------------------------
# parse_html — Cursor adapter (cursor.com/careers/<slug>)
# ---------------------------------------------------------------------------


def test_parse_html_cursor_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["title"] == "Software Engineer, ML Infrastructure"


def test_parse_html_cursor_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["company_name"] == "Cursor"


def test_parse_html_cursor_location_from_header_p() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["location"] == "San Francisco; New York"


def test_parse_html_cursor_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["description"] is not None
    assert "ML Infrastructure" in result["description"]


def test_parse_html_cursor_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("cursor_job.html")
    result = parse_html(html, "https://cursor.com/careers/software-engineer-ml-infrastructure")
    assert result["role_type"] == "full-time"


# ---------------------------------------------------------------------------
# parse_html — Pinecone adapter (pinecone.io/careers/<uuid>/)
# ---------------------------------------------------------------------------


def test_parse_html_pinecone_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["title"] == "Senior/Staff Software Engineer, Database Team"


def test_parse_html_pinecone_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["company_name"] == "Pinecone"


def test_parse_html_pinecone_location_from_at_p() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["location"] == "New York City"


def test_parse_html_pinecone_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinecone_job.html")
    result = parse_html(
        html, "https://www.pinecone.io/careers/4ef4269b-94c4-4c7c-93ee-15a882caa767/"
    )
    assert result["description"] is not None
    assert "Pinecone" in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Lever adapter (jobs.lever.co/<company>/<id>)
# ---------------------------------------------------------------------------


def test_parse_html_lever_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["title"] == "AI Engineer, Product"


def test_parse_html_lever_company_from_title_tag() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["company_name"] == "Mistral AI"


def test_parse_html_lever_location_first_category() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["location"] == "Paris"


def test_parse_html_lever_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["role_type"] == "full-time"


def test_parse_html_lever_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("lever_job.html")
    result = parse_html(html, "https://jobs.lever.co/mistral/c79ff8ed-6689-4dda-aec6-979a5dc767d0")
    assert result["description"] is not None
    assert "Mistral" in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Pinterest adapter (pinterestcareers.com/jobs/<id>/<slug>/)
# ---------------------------------------------------------------------------


def test_parse_html_pinterest_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["title"] == "Staff Machine Learning Engineer, Ads Conversion"


def test_parse_html_pinterest_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["company_name"] == "Pinterest"


def test_parse_html_pinterest_location_from_first_li() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["location"] == "San Francisco / Palo Alto / Seattle"


def test_parse_html_pinterest_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["role_type"] == "full-time"


def test_parse_html_pinterest_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("pinterest_job.html")
    result = parse_html(
        html,
        "https://www.pinterestcareers.com/jobs/7902034/staff-machine-learning-engineer-ads-conversion/?gh_jid=7902034",
    )
    assert result["description"] is not None
    assert "Machine Learning" in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Workable adapter (jobs.workable.com)
# ---------------------------------------------------------------------------


def test_parse_html_workable_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["title"] == "Senior Full-stack Software Engineer"


def test_parse_html_workable_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["company_name"] == "Kettle"


def test_parse_html_workable_location_with_remote() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["location"] == "San Francisco (Remote)"


def test_parse_html_workable_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["role_type"] == "full-time"


def test_parse_html_workable_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_job.html")
    result = parse_html(
        html,
        "https://jobs.workable.com/en/view/jo82yMiX7GNRYQ4RpFWFaN/hybrid-senior-full-stack-software-engineer-in-san-francisco-at-kettle",
    )
    assert result["description"] is not None
    assert "Kettle" in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Notion adapter (*.notion.site/<page-id>)
# Fixture: notion_paradedb_job.html — ParadeDB Distributed Systems Engineer
# ---------------------------------------------------------------------------

_NOTION_URL = "https://paradedb.notion.site/Distributed-Systems-Engineer-Postgres-Platform-1a5ea4ce9deb80aeb0ddd5cbbd10f654"


def test_parse_html_notion_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["title"] == "Distributed Systems Engineer — Postgres Platform"


def test_parse_html_notion_company_from_breadcrumb() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["company_name"] == "ParadeDB"


def test_parse_html_notion_location_from_property() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["location"] == "Remote, San Francisco"


def test_parse_html_notion_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["role_type"] == "full-time"


def test_parse_html_notion_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["description"] is not None
    assert "ParadeDB" in result["description"]
    assert "Postgres" in result["description"]


def test_match_adapter_notion_site_suffix() -> None:
    from jobforce.services.parse import SITE_ADAPTERS, _match_adapter

    assert "notion.site" in SITE_ADAPTERS
    assert _match_adapter("paradedb.notion.site") is SITE_ADAPTERS["notion.site"]


# ---------------------------------------------------------------------------
# AdaL (adalagent.ai) — custom React SPA
# ---------------------------------------------------------------------------

_ADAL_URL = "https://adalagent.ai/jobs/mts-production-quality"


def test_parse_html_adal_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["title"] == "Member of Technical Staff - Production Quality"


def test_parse_html_adal_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["company_name"] == "AdaL"


def test_parse_html_adal_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["location"] == "San Francisco, United States"


def test_parse_html_adal_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("adal_job.html")
    result = parse_html(html, _ADAL_URL)
    assert result["description"] is not None
    assert "Production Quality" in result["description"]


# ---------------------------------------------------------------------------
# Discord (discord.com/jobs/<id>)
# ---------------------------------------------------------------------------

_DISCORD_URL = "https://discord.com/jobs/8136321002"


def test_parse_html_discord_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["title"] == "Senior Software Engineer - Platform Infrastructure"


def test_parse_html_discord_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["company_name"] == "Discord"


def test_parse_html_discord_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["location"] == "San Francisco Bay Area"


def test_parse_html_discord_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["description"] is not None
    assert "distributed systems" in result["description"]
