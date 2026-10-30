"""Unit tests for the Greenhouse (boards/job-boards.greenhouse.io) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


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


def test_parse_html_greenhouse_eu_subdomain() -> None:
    # job-boards.eu.greenhouse.io (e.g. Groww) is the same Greenhouse product
    # on an EU-region host — was missing from HOSTNAMES entirely, so
    # company_name (parsed from the URL path) never ran.
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://job-boards.eu.greenhouse.io/groww/jobs/4728765101")
    assert result["company_name"] == "Groww"


def test_parse_html_greenhouse_detects_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result["role_type"] == "full-time"


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
# parse_html — posted_at from the embedded Remix payload (Figma)
# ---------------------------------------------------------------------------


def test_parse_html_greenhouse_posted_at_from_remix_context() -> None:
    from jobforce.services.parse import parse_html

    html = _read("figma_greenhouse_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/figma/jobs/5551532004")
    assert result["posted_at"] == "2025-06-02"


def test_parse_html_greenhouse_posted_at_none_when_absent() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    result = parse_html(html, "https://boards.greenhouse.io/stripe/jobs/12345")
    assert result.get("posted_at") is None


def test_parse_html_greenhouse_embed_url_uses_for_param_for_company() -> None:
    """boards.greenhouse.io/embed/job_app?for=<slug>&token=<id> has no company
    in its path; use the `for` board slug (trailing digits stripped, e.g.
    digitalocean98 -> Digitalocean) instead of the literal "Embed"."""
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_job.html")
    url = "https://boards.greenhouse.io/embed/job_app?for=digitalocean98&token=7790123002"
    result = parse_html(html, url)
    assert result["company_name"] == "Digitalocean"


# ---------------------------------------------------------------------------
# parse_html — application-only board layout (Patronus AI): the page renders
# only the apply form (no h1 / .job__title / .job__location / .job__description);
# the job itself lives in the inline Remix `jobPost` payload.
# ---------------------------------------------------------------------------

_PATRONUS_URL = "https://job-boards.greenhouse.io/patronusaiinc/jobs/4412230009"


def test_parse_html_greenhouse_patronus_title_from_job_post_payload() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("greenhouse_patronus_job.html"), _PATRONUS_URL)
    assert result["title"] == "Member of Technical Staff - Engineering"


def test_parse_html_greenhouse_patronus_location_from_job_post_payload() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("greenhouse_patronus_job.html"), _PATRONUS_URL)
    assert result["location"] == "San Francisco"


def test_parse_html_greenhouse_patronus_company_from_job_post_payload() -> None:
    # Slug "patronusaiinc" is a squashed form of the payload's company_name
    # "Patronus AI, Inc." — prefer the real name, minus the legal suffix.
    from jobforce.services.parse import parse_html

    result = parse_html(_read("greenhouse_patronus_job.html"), _PATRONUS_URL)
    assert result["company_name"] == "Patronus AI"


def test_parse_html_greenhouse_patronus_description_from_job_post_payload() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("greenhouse_patronus_job.html"), _PATRONUS_URL)
    assert result["description"] is not None
    assert "agent trajectories" in result["description"]
    # Must not fall back to an application-form question's helper text.
    assert "Twitter" not in result["description"]


def test_parse_html_greenhouse_patronus_normalizes_nbsp_in_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_patronus_job.html").replace(
        "Member of Technical Staff - Engineering", "Member of Technical Staff - Engineering"
    )
    result = parse_html(html, _PATRONUS_URL)
    assert result["title"] == "Member of Technical Staff - Engineering"


def test_parse_html_greenhouse_company_keeps_slug_when_payload_name_unrelated() -> None:
    # Payload company_name is only trusted when it is a reformatting of the URL
    # slug — otherwise keep the slug-derived name so existing company records
    # keep matching.
    from jobforce.services.parse import parse_html

    html = _read("greenhouse_patronus_job.html")
    result = parse_html(html, "https://job-boards.greenhouse.io/acme/jobs/1")
    assert result["company_name"] == "Acme"
