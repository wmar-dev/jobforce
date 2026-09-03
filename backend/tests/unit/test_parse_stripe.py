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
