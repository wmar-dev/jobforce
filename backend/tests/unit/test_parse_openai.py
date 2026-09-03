"""Unit tests for the OpenAI (openai.com) site adapter in parse/sites/openai.py."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


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
