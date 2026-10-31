"""Unit tests for the Etsy (careers.etsy.com) adapter — no `og:site_name` or
company element (so company_name is None and scout_fetch rejects the page),
and the generic `.location` selector hits the referral form's Location
dropdown instead of the job's own location. The ld+json JobPosting block has
the hiring organization, location (plus a TELECOMMUTE flag for remote-open
roles) and full description.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_ETSY_URL = "https://careers.etsy.com/jobs/senior-staff-machine-learning-engineer-brooklyn-new-york-united-states"


def test_parse_html_etsy_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("etsy_job.html")
    result = parse_html(html, _ETSY_URL)
    assert result["company_name"] == "Etsy"


def test_parse_html_etsy_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("etsy_job.html")
    result = parse_html(html, _ETSY_URL)
    assert result["location"] == "Brooklyn, New York; Remote"


def test_parse_html_etsy_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("etsy_job.html")
    result = parse_html(html, _ETSY_URL)
    assert result["description"] is not None
    assert "lead ranking for Etsy search" in result["description"]
