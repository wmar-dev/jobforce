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


def test_openai_gov_location_job_multi_location_from_subhead() -> None:
    """Current OpenAI hero markup wraps the subhead <p> in a <div> after the title
    h2 instead of making it a direct sibling, so the old find_next_sibling("p")
    lookup misses it entirely for pages like this 3-location gov posting."""
    from jobforce.services.parse import parse_html

    html = _read("openai_gov_location_job.html")
    result = parse_html(
        html,
        "https://openai.com/careers/senior-staff-software-engineer-gov-washington-dc/",
    )
    assert result["location"] is not None
    assert "Washington, DC" in result["location"]
    assert "San Francisco" in result["location"]


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


def test_parse_html_workday_title_falls_back_to_job_posting_header() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job_dl_locations.html")
    result = parse_html(
        html,
        "https://verily.wd1.myworkdayjobs.com/en-US/Verily_Careers/job/San-Bruno-California/Staff-AI-Applied-Scientist_REQ-723",
    )
    assert result["title"] == "Staff AI Applied Scientist"


def test_parse_html_workday_location_falls_back_to_dl_dd_list() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workday_job_dl_locations.html")
    result = parse_html(
        html,
        "https://verily.wd1.myworkdayjobs.com/en-US/Verily_Careers/job/San-Bruno-California/Staff-AI-Applied-Scientist_REQ-723",
    )
    assert (
        result["location"]
        == "San Bruno, California; Boston, Massachusetts; Mountain View, California"
    )


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


def test_parse_html_ashby_frontcareers_slug_maps_to_front() -> None:
    """Front's Ashby board slug is 'frontcareers', not 'front'."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/frontcareers/xyz-456")
    assert result["company_name"] == "Front"


def test_parse_html_ashby_grammarly_slug_maps_to_grammarly() -> None:
    """Grammarly's Ashby board slug is its parent brand's legal entity name,
    URL-encoded with spaces (%20) since it contains real spaces."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/Superhuman%20Platform%20Inc/xyz-456")
    assert result["company_name"] == "Grammarly"


def test_parse_html_ashby_url_encoded_slug_decoded_before_capitalizing() -> None:
    """A %20-encoded slug with no override should still decode to real words
    rather than leaking literal '%20' into the capitalized company name."""
    from jobforce.services.parse import parse_html

    html = _read("ashby_job.html")
    result = parse_html(html, "https://jobs.ashbyhq.com/Acme%20Corp/xyz-456")
    assert result["company_name"] == "Acme Corp"


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


_WORKABLE_APPLY_URL = "https://apply.workable.com/innovaccer-analytics/j/643DCD9804/"


def test_parse_html_workable_apply_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_apply_innovaccer_job.html")
    result = parse_html(html, _WORKABLE_APPLY_URL)
    assert result["company_name"] == "Innovaccer Analytics"


def test_parse_html_workable_apply_location_handles_list_jobLocation() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_apply_innovaccer_job.html")
    result = parse_html(html, _WORKABLE_APPLY_URL)
    assert result["location"] == "San Francisco, California"


def test_parse_html_workable_apply_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("workable_apply_innovaccer_job.html")
    result = parse_html(html, _WORKABLE_APPLY_URL)
    assert result["description"] is not None
    assert "production-grade AI systems" in result["description"]


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
# Larridin (larridin.com) — HubSpot CMS page; company name, location, and
# description all live in custom markup with no generic-adapter hooks
# ---------------------------------------------------------------------------

_LARRIDIN_URL = "https://larridin.com/software-engineer"


def test_parse_html_larridin_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("larridin_job.html")
    result = parse_html(html, _LARRIDIN_URL)
    assert result["company_name"] == "Larridin"


def test_parse_html_larridin_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("larridin_job.html")
    result = parse_html(html, _LARRIDIN_URL)
    assert result["location"] == "Bay Area | In-Office"


def test_parse_html_larridin_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("larridin_job.html")
    result = parse_html(html, _LARRIDIN_URL)
    assert result["description"] is not None
    assert "AI-native engineering teams that own outcomes" in result["description"]


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


# ---------------------------------------------------------------------------
# Stripe (stripe.com/jobs/listing/<slug>/<id>)
# ---------------------------------------------------------------------------

_STRIPE_URL = (
    "https://stripe.com/jobs/listing/android-engineer-terminal-developer-productivity/7550154"
)


def test_parse_html_stripe_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_job.html")
    result = parse_html(html, _STRIPE_URL)
    assert result["title"] == "Android Engineer, Terminal Developer Productivity"


def test_parse_html_stripe_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_job.html")
    result = parse_html(html, _STRIPE_URL)
    assert result["company_name"] == "Stripe"


def test_parse_html_stripe_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_job.html")
    result = parse_html(html, _STRIPE_URL)
    assert result["location"] == "Seattle,  or South San Francisco HQ"


def test_parse_html_stripe_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_job.html")
    result = parse_html(html, _STRIPE_URL)
    assert result["role_type"] == "full-time"


def test_parse_html_stripe_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_job.html")
    result = parse_html(html, _STRIPE_URL)
    assert result["description"] is not None
    assert "Developer Productivity team" in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Turing adapter (careers.turing.com/job/<id>)
# ---------------------------------------------------------------------------

_TURING_URL = "https://careers.turing.com/job/5609732004"


def test_parse_html_turing_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert result["company_name"] == "Turing"


def test_parse_html_turing_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert result["title"] == "Forward Deployed AI Engineer"


def test_parse_html_turing_location_strips_prefix() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert (
        result["location"]
        == "New York, New York, United States; San Francisco, California, United States"
    )


def test_parse_html_turing_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("turing_job.html")
    result = parse_html(html, _TURING_URL)
    assert result["description"] is not None
    assert "Generative AI" in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Waymo adapter (careers.withwaymo.com/jobs/<slug>)
# ---------------------------------------------------------------------------

_WAYMO_URL = "https://careers.withwaymo.com/jobs/machine-learning-engineer-perception-llm-vlm"


def test_parse_html_waymo_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("waymo_job.html")
    result = parse_html(html, _WAYMO_URL)
    assert result["company_name"] == "Waymo"


def test_parse_html_waymo_title_ignores_sitewide_headings() -> None:
    from jobforce.services.parse import parse_html

    html = _read("waymo_job.html")
    result = parse_html(html, _WAYMO_URL)
    assert result["title"] == "Machine Learning Engineer Perception LLM/VLM (PhD, New Grad)"


def test_parse_html_waymo_location_ignores_related_jobs_sidebar() -> None:
    from jobforce.services.parse import parse_html

    html = _read("waymo_job.html")
    result = parse_html(html, _WAYMO_URL)
    assert result["location"] == "Mountain View, California, San Francisco, California"


# ---------------------------------------------------------------------------
# parse_html — Warner Bros. Discovery adapter (careers.wbd.com, Phenom People ATS)
# ---------------------------------------------------------------------------

_WBD_URL = "https://careers.wbd.com/global/en/job/R000106532/Staff-Machine-Learning-Engineer-Search"


def test_parse_html_wbd_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["company_name"] == "Warner Bros. Discovery"


def test_parse_html_wbd_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["title"] == "Staff Machine Learning Engineer -  Search"


def test_parse_html_wbd_location_joins_all_and_dedupes() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["location"] == (
        "San Francisco, California, United States of America; "
        "Bellevue, Washington, United States of America"
    )


def test_parse_html_wbd_description_excludes_similar_jobs_and_share_widgets() -> None:
    from jobforce.services.parse import parse_html

    html = _read("wbd_job.html")
    result = parse_html(html, _WBD_URL)
    assert result["description"] is not None
    assert "Staff Machine Learning Engineer" in result["description"]
    assert "Similar Jobs" not in result["description"]
    assert "Share this opportunity" not in result["description"]


# ---------------------------------------------------------------------------
# parse_html — Google Careers adapter (google.com/about/careers/applications/jobs/results/<slug>)
# ---------------------------------------------------------------------------

_GOOGLE_CAREERS_URL = (
    "https://www.google.com/about/careers/applications/jobs/results/"
    "136775056809173702-senior-software-engineer-aiml-creative-intelligence"
)


def test_parse_html_google_careers_company_name() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["company_name"] == "Google"


def test_parse_html_google_careers_title_ignores_sitewide_heading() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["title"] == "Senior Software Engineer, AI/ML, Creative Intelligence"


def test_parse_html_google_careers_location_strips_icon_ligature() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["location"] == "Mountain View, CA, USA"


def test_parse_html_google_careers_description_excludes_boilerplate() -> None:
    from jobforce.services.parse import parse_html

    html = _read("google_careers_job.html")
    result = parse_html(html, _GOOGLE_CAREERS_URL)
    assert result["description"] is not None
    assert "Generative AI" in result["description"]
    assert "Privacy Policy" not in result["description"]
    assert "equal opportunity" not in result["description"]


# ---------------------------------------------------------------------------
# C3.ai (c3.ai) — Next.js job page. Title is a bare <h1>, location/department
# share one <p> right after it ("City, ST · Department"), and the full JD
# (intro, responsibilities, pay range, EEO conclusion) lives in the wrapper
# <div> that follows the "Apply Now" button.
# ---------------------------------------------------------------------------

_C3AI_URL = "https://c3.ai/job-description?gh_jid=6225305002"


def test_parse_html_c3ai_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("c3ai_job.html")
    result = parse_html(html, _C3AI_URL)
    assert result["company_name"] == "C3 AI"


def test_parse_html_c3ai_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("c3ai_job.html")
    result = parse_html(html, _C3AI_URL)
    assert result["location"] == "Redwood City, CA"


def test_parse_html_c3ai_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("c3ai_job.html")
    result = parse_html(html, _C3AI_URL)
    assert result["description"] is not None
    assert "AI Studio team" in result["description"]
    assert "Equal Opportunity" in result["description"]


# ---------------------------------------------------------------------------
# Rippling ATS (ats.rippling.com/<company-slug>/jobs/<id>) — shared job board
# used by many companies (e.g. ThoughtSpot, Rippling itself). The recruiter-
# authored description HTML sometimes embeds the next section's heading
# inside the same malformed <h1> as the job title, so title comes from the
# document <title> tag instead. There's no structured company name field on
# the job page; it's derived from the breadcrumb link back to the employer's
# own careers site.
# ---------------------------------------------------------------------------

_RIPPLING_THOUGHTSPOT_URL = (
    "https://ats.rippling.com/thoughtspot/jobs/602db28c-e76f-4fee-ad02-0419372d02af"
)


def test_parse_html_rippling_title_ignores_embedded_next_heading() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["title"] == "Staff Forward Deployment Engineer"


def test_parse_html_rippling_company_from_breadcrumb() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["company_name"] == "Thoughtspot"


def test_parse_html_rippling_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["location"] == "Mountain View, CA"


def test_parse_html_rippling_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("rippling_thoughtspot_job.html")
    result = parse_html(html, _RIPPLING_THOUGHTSPOT_URL)
    assert result["description"] is not None
    assert "Agentic Analytics Platform" in result["description"]


# ---------------------------------------------------------------------------
# Twilio (jobs.twilio.com) — Eightfold-powered ATS on Twilio's own domain.
# The page's static <h1> always reads "Single Position" regardless of which
# job is loaded; the real title lives in an <h2> further down.
# ---------------------------------------------------------------------------

_TWILIO_URL = "https://jobs.twilio.com/careers/job/1099554769400"


def test_parse_html_twilio_title_ignores_static_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["title"] == "Senior Software Engineer"


def test_parse_html_twilio_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["company_name"] == "Twilio"


def test_parse_html_twilio_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["location"] == "Remote - US"


def test_parse_html_twilio_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("twilio_job.html")
    result = parse_html(html, _TWILIO_URL)
    assert result["description"] is not None
    assert "data infrastructure" in result["description"]


# ---------------------------------------------------------------------------
# Nebius (careers.nebius.com) — scout_fetch synthesizes this HTML shape from
# Greenhouse's public Jobs API (see _fetch_nebius_greenhouse_html) since the
# real page hides everything in a cross-origin iframe.
# ---------------------------------------------------------------------------

_NEBIUS_URL = "https://careers.nebius.com/?gh_jid=4765610101"


def test_parse_html_nebius_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["title"] == "Infrastructure Software Engineer"


def test_parse_html_nebius_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["company_name"] == "Nebius"


def test_parse_html_nebius_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["location"] == "Remote - United States"


def test_parse_html_nebius_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("nebius_job.html")
    result = parse_html(html, _NEBIUS_URL)
    assert result["description"] is not None
    assert "bare-metal infrastructure" in result["description"]


# ---------------------------------------------------------------------------
# Asana (asana.com/jobs/apply/<id>) — title parses fine via the generic
# adapter's <h1> selector, but company_name falls back to the wrong
# og:site_name ("Asana Jobs") and location/description need dedicated
# selectors since they're not tagged with any location/description class.
# ---------------------------------------------------------------------------

_ASANA_URL = "https://asana.com/jobs/apply/8084470"


def test_parse_html_asana_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["title"] == "Senior Software Engineer, Infrastructure Security"


def test_parse_html_asana_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["company_name"] == "Asana"


def test_parse_html_asana_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_asana_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("asana_job.html")
    result = parse_html(html, _ASANA_URL)
    assert result["description"] is not None
    assert "Security Development team" in result["description"]


# ---------------------------------------------------------------------------
# Breezy HR (<company>.breezy.hr/p/<id>-<slug>) — shared ATS. The page has
# two <h1>s (site brand logo, then the real job title), so the generic
# adapter's bare "h1" selector picks up the wrong one. Company name is
# derived from the subdomain, same pattern as the Workday adapter.
# ---------------------------------------------------------------------------

_BREEZY_BEARROBOTICS_URL = "https://bear-robotics.breezy.hr/p/58d3df356ee1-software-engineer-ii"


def test_parse_html_breezy_title_ignores_brand_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["title"] == "Software Engineer II"


def test_parse_html_breezy_company_from_subdomain() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["company_name"] == "Bear Robotics"


def test_parse_html_breezy_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["location"] == "Redwood City, CA"


def test_parse_html_breezy_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("breezy_bearrobotics_job.html")
    result = parse_html(html, _BREEZY_BEARROBOTICS_URL)
    assert result["description"] is not None
    assert "designing, developing, and maintaining complex software" in result["description"]


# ---------------------------------------------------------------------------
# Block (block.xyz/careers/jobs/<id>) — the site's own og:site_name meta is
# buggy and echoes the page title instead of "Block", so the generic
# adapter's company_name fallback grabs the wrong text; location and
# description need dedicated selectors too.
# ---------------------------------------------------------------------------

_BLOCK_URL = "https://block.xyz/careers/jobs/5243440008"


def test_parse_html_block_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["title"] == "Senior Machine Learning Engineer, Applied AI Quality"


def test_parse_html_block_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["company_name"] == "Block"


def test_parse_html_block_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["location"] == "Bay Area, CA, US"


def test_parse_html_block_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["description"] is not None
    assert "Applied AI Quality team" in result["description"]


# ---------------------------------------------------------------------------
# Brex (brex.com/careers/<id>) — title and company_name already extract
# correctly via the generic adapter; location is a bare <h4>, and the
# description sits in the parent of Greenhouse's ".content-intro" wrapper
# div (this page renders Greenhouse's job content HTML directly).
# ---------------------------------------------------------------------------

_BREX_URL = "https://www.brex.com/careers/8606890002"


def test_parse_html_brex_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brex_job.html")
    result = parse_html(html, _BREX_URL)
    assert result["title"] == "AI Engineer, Ecosystem"


def test_parse_html_brex_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brex_job.html")
    result = parse_html(html, _BREX_URL)
    assert result["location"] == "San Francisco, California, United States"


def test_parse_html_brex_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("brex_job.html")
    result = parse_html(html, _BREX_URL)
    assert result["description"] is not None
    assert "agentic integrations" in result["description"]


# ---------------------------------------------------------------------------
# Chime (careers.chime.com/jobs/<id>/<slug>) — title extracts fine via the
# generic adapter's <h1>; company_name, location, and description need
# overrides. Location is the second of two <p> tags inside
# ".content-wrapper" (department, then location); description is the
# ".jobCopy" container.
# ---------------------------------------------------------------------------

_CHIME_URL = "https://careers.chime.com/jobs/8569366002/senior-ai-ml-engineer"


def test_parse_html_chime_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert result["title"] == "Senior AI/ML Engineer"


def test_parse_html_chime_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert result["company_name"] == "Chime"


def test_parse_html_chime_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert (
        result["location"]
        == "Chicago, IL, USA; New York, NY, USA; San Francisco, CA, USA; Seattle, WA, USA"
    )


def test_parse_html_chime_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert result["description"] is not None
    assert "Growth & Marketing AI" in result["description"]


# ---------------------------------------------------------------------------
# Coinbase (coinbase.com/careers/positions/<id>) — title extracts fine via
# the generic adapter's <h1>. Location is the first of two <span> tags in
# the div right after the <h1> (location, then Job ID); Coinbase renders
# Greenhouse's job content HTML directly, including its ".content-intro"
# wrapper div, so the description container is that div's parent — same
# pattern as Brex.
# ---------------------------------------------------------------------------

_COINBASE_URL = "https://www.coinbase.com/careers/positions/7739592"


def test_parse_html_coinbase_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["title"] == "Senior Machine Learning Engineer"


def test_parse_html_coinbase_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["company_name"] == "Coinbase"


def test_parse_html_coinbase_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["location"] == "Remote - USA"


def test_parse_html_coinbase_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("coinbase_job.html")
    result = parse_html(html, _COINBASE_URL)
    assert result["description"] is not None
    assert "models that power Coinbase's core products" in result["description"]


# ---------------------------------------------------------------------------
# Intuit (jobs.intuit.com/job/<city>/<slug>/27595/<id>) — shared board across
# all Intuit brands (Credit Karma, TurboTax, QuickBooks, Mailchimp). Title
# already extracts fine via the generic adapter's <h1>, which carries a
# " - <Brand>" suffix company_name is derived from. The generic adapter's
# location falls back to "Multiple Locations" from page metadata instead of
# reading the real ".job-location-jd" element.
# ---------------------------------------------------------------------------

_INTUIT_CK_URL = (
    "https://jobs.intuit.com/job/charlotte/staff-software-engineer-credit-karma/27595/99074782144"
)


def test_parse_html_intuit_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("intuit_creditkarma_job.html")
    result = parse_html(html, _INTUIT_CK_URL)
    assert result["title"] == "Staff Software Engineer - Credit Karma"


def test_parse_html_intuit_company_from_title_suffix() -> None:
    from jobforce.services.parse import parse_html

    html = _read("intuit_creditkarma_job.html")
    result = parse_html(html, _INTUIT_CK_URL)
    assert result["company_name"] == "Credit Karma"


def test_parse_html_intuit_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("intuit_creditkarma_job.html")
    result = parse_html(html, _INTUIT_CK_URL)
    assert (
        result["location"]
        == "Charlotte, North Carolina; Mountain View, California; Oakland, California"
    )


# ---------------------------------------------------------------------------
# Docusign (careers.docusign.com/careers-home/jobs/<id>) — title and
# description already extract fine via the generic adapter; the site's own
# og:site_name meta is buggy and echoes the full "<title> in <location> |
# careers-home" page title instead of "Docusign". "#job-location" only
# shows one arbitrary location from a multi-location posting, so location
# comes from "#header-locations" instead, which carries the full list.
# ---------------------------------------------------------------------------

_DOCUSIGN_URL = "https://careers.docusign.com/careers-home/jobs/29733"


def test_parse_html_docusign_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("docusign_job.html")
    result = parse_html(html, _DOCUSIGN_URL)
    assert result["title"] == "Senior Software Engineer - New Revenue"


def test_parse_html_docusign_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("docusign_job.html")
    result = parse_html(html, _DOCUSIGN_URL)
    assert result["company_name"] == "Docusign"


def test_parse_html_docusign_location_prefers_full_multi_location_list() -> None:
    from jobforce.services.parse import parse_html

    html = _read("docusign_job.html")
    result = parse_html(html, _DOCUSIGN_URL)
    assert result["location"] == "San Francisco, California; Seattle, Washington"


# ---------------------------------------------------------------------------
# DoorDash (careersatdoordash.com/jobs/<slug>/<id>) — title and company_name
# already extract fine via the generic adapter; location and description
# need dedicated selectors ("#jd-location" and ".content").
# ---------------------------------------------------------------------------

_DOORDASH_URL = "https://careersatdoordash.com/jobs/software-engineer-data-and-ai-platform/8171620"


def test_parse_html_doordash_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("doordash_job.html")
    result = parse_html(html, _DOORDASH_URL)
    assert result["title"] == "SOFTWARE ENGINEER, DATA AND AI PLATFORM"


def test_parse_html_doordash_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("doordash_job.html")
    result = parse_html(html, _DOORDASH_URL)
    assert result["location"] == "San Francisco, CA; Sunnyvale, CA"


def test_parse_html_doordash_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("doordash_job.html")
    result = parse_html(html, _DOORDASH_URL)
    assert result["description"] is not None
    assert "drill-down and cross-filter semantics" in result["description"]


# ---------------------------------------------------------------------------
# Dropbox (dropbox.jobs/en/jobs/<id>/<slug>) — company_name and location come
# from the page's own "#js-job-posting" schema.org JobPosting JSON-LD block
# (same pattern as the Workable adapter), since the generic adapter's
# og:site_name only yields the generic "Dropbox Careers" and there's no
# plain-text location element.
# ---------------------------------------------------------------------------

_DROPBOX_URL = "https://www.dropbox.jobs/en/jobs/8006972/principal-software-engineer-core-sharing-collaboration/"


def test_parse_html_dropbox_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("dropbox_job.html")
    result = parse_html(html, _DROPBOX_URL)
    assert result["company_name"] == "Dropbox"


def test_parse_html_dropbox_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("dropbox_job.html")
    result = parse_html(html, _DROPBOX_URL)
    assert result["location"] == "Remote - US: All locations"


def test_parse_html_dropbox_description_from_jsonld() -> None:
    """The generic adapter finds no plain-text description container on this
    React-rendered page; description must come from the JSON-LD block."""
    from jobforce.services.parse import parse_html

    html = _read("dropbox_job.html")
    result = parse_html(html, _DROPBOX_URL)
    assert result["description"] is not None
    assert "Principal Engineer at Dropbox" in result["description"]


# ---------------------------------------------------------------------------
# GitHub (www.github.careers/careers-home/jobs/<id>) — a Phenom People/iCIMS
# board (same "#header-locations" pattern seen on careers.docusign.com).
# company_name comes back from the generic adapter as the full page <title>
# ("<role> in <location> | GitHub, Inc."), and location isn't visible via
# any plain element the generic adapter checks.
# ---------------------------------------------------------------------------

_GITHUB_URL = "https://www.github.careers/careers-home/jobs/5679?lang=en-us"


def test_parse_html_github_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("github_job.html")
    result = parse_html(html, _GITHUB_URL)
    assert result["company_name"] == "GitHub"


def test_parse_html_github_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("github_job.html")
    result = parse_html(html, _GITHUB_URL)
    assert result["location"] == "United States"


# ---------------------------------------------------------------------------
# Grid Dynamics (griddynamics.com/careers/vacancy/<id>) — title extracts fine
# via the generic adapter, but location isn't visible via any plain element
# the generic adapter checks, and the generic adapter's description falls
# back to the short meta description rather than the full vacancy body.
# ---------------------------------------------------------------------------

_GRIDDYNAMICS_URL = "https://www.griddynamics.com/careers/vacancy/59817"


def test_parse_html_griddynamics_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("griddynamics_job.html")
    result = parse_html(html, _GRIDDYNAMICS_URL)
    assert result["location"] == "US Remote, US"


# ---------------------------------------------------------------------------
# Guidewire (guidewire.com/about/careers/jobs/<slug>) — no <h1>; the page
# uses <h2> for the job title, so the generic adapter falls back to the
# <title> tag and truncates at the first " - ", dropping team-qualifier
# suffixes like "- Cloud Data Platform" from titles that legitimately
# contain a hyphen. Location and description aren't exposed via any plain
# element the generic adapter checks — its description fallback picks up
# the site's footer boilerplate ("We do not accept bot-generated candidate
# applications...") instead.
# ---------------------------------------------------------------------------

_GUIDEWIRE_URL = "https://www.guidewire.com/about/careers/jobs/senior-software-engineer---cloud-data-platform-jr_14462"


def test_parse_html_guidewire_title_full_not_truncated_at_hyphen() -> None:
    from jobforce.services.parse import parse_html

    html = _read("guidewire_job.html")
    result = parse_html(html, _GUIDEWIRE_URL)
    assert result["title"] == "Senior Software Engineer - Cloud Data Platform"


def test_parse_html_guidewire_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("guidewire_job.html")
    result = parse_html(html, _GUIDEWIRE_URL)
    assert result["location"] == "United States - San Mateo, CA"


def test_parse_html_guidewire_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("guidewire_job.html")
    result = parse_html(html, _GUIDEWIRE_URL)
    assert result["description"] is not None
    assert "machine learning lifecycle" in result["description"]


def test_parse_html_griddynamics_description_prefers_full_body_over_meta() -> None:
    """The generic adapter falls back to the short <meta name="description">
    tag, which drops the "Essential functions" list present in the full
    vacancy body."""
    from jobforce.services.parse import parse_html

    html = _read("griddynamics_job.html")
    result = parse_html(html, _GRIDDYNAMICS_URL)
    assert result["description"] is not None
    assert "Essential functions" in result["description"]
