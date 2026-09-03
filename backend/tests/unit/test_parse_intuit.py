"""Unit tests for the Intuit (jobs.intuit.com/job/<city>/<slug>/27595/<id>) site
adapter — shared board across all Intuit brands (Credit Karma, TurboTax,
QuickBooks, Mailchimp). Title already extracts fine via the generic adapter's
<h1>, which carries a " - <Brand>" suffix company_name is derived from. The
generic adapter's location falls back to "Multiple Locations" from page
metadata instead of reading the real ".job-location-jd" element.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


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
