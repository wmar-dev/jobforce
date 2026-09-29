"""Unit tests for the Stripe (stripe.com/jobs/listing/<slug>/<id>) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


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


# Stripe redesigned careers.stripe.com to /careers/listing/<slug>/<id> with a
# new "hds-" design system — .Copy__header, .JobDetailCardProperty__title,
# and .ArticleMarkdown no longer exist on this layout.
_STRIPE_NEW_LAYOUT_URL = (
    "https://stripe.com/careers/listing/senior-staff-software-engineer-stripe-dashboard/7746721"
)


def test_parse_html_stripe_new_layout_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_new_layout_job.html")
    result = parse_html(html, _STRIPE_NEW_LAYOUT_URL)
    assert result["location"] == "Toronto, New York, Seattle, South San Francisco HQ"


def test_parse_html_stripe_new_layout_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_new_layout_job.html")
    result = parse_html(html, _STRIPE_NEW_LAYOUT_URL)
    assert result["description"] is not None
    assert "Merchant Experience team" in result["description"]


# Some new-layout listings use the singular "Office location" label instead
# of "Office locations" — a plain equality check on the label missed these.
_STRIPE_SINGULAR_OFFICE_URL = (
    "https://stripe.com/careers/listing/staff-software-engineer-risk-data-engineering/8112043"
)


def test_parse_html_stripe_singular_office_location_label() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_new_layout_singular_office_job.html")
    result = parse_html(html, _STRIPE_SINGULAR_OFFICE_URL)
    assert result["location"] == "Toronto"


# Fully-remote new-layout listings have no "Office location(s)" fact at all —
# fall back to "Remote location" rather than returning None.
_STRIPE_REMOTE_ONLY_URL = (
    "https://stripe.com/careers/listing/software-engineer-secrets-infrastructure/7396679"
)


def test_parse_html_stripe_remote_only_location_fallback() -> None:
    from jobforce.services.parse import parse_html

    html = _read("stripe_new_layout_remote_only_job.html")
    result = parse_html(html, _STRIPE_REMOTE_ONLY_URL)
    assert result["location"] == "Remote in United States"
