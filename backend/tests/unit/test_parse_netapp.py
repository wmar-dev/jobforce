"""Unit tests for the NetApp (careers.netapp.com) site adapter — a Radancy
Talentbrew-templated career site. The page has two <h1> elements: a generic
marketing hero tagline that appears first in the DOM, and the real job title
further down (`h1.ajd_header__job-title`) — the generic adapter's bare "h1"
selector grabs the hero tagline instead. There's also no `og:site_name` (or
any company element), so company_name comes back null. location and
description already extract correctly via the generic adapter's class
selectors (`.job-location`, `[class*="description"]`), so no override is
needed for those.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_NETAPP_URL = "https://careers.netapp.com/job/waltham/software-engineer/27600/100011360240"


def test_parse_html_netapp_title_overrides_hero_heading() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netapp_job.html")
    result = parse_html(html, _NETAPP_URL)
    assert result["title"] == "Software Engineer"


def test_parse_html_netapp_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netapp_job.html")
    result = parse_html(html, _NETAPP_URL)
    assert result["company_name"] == "NetApp"


def test_parse_html_netapp_location_via_generic_adapter() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netapp_job.html")
    result = parse_html(html, _NETAPP_URL)
    assert (
        result["location"]
        == "Waltham, Massachusetts, United States; San Jose, California, United States; "
        "Morrisville, North Carolina, United States"
    )


def test_parse_html_netapp_description_via_generic_adapter() -> None:
    from jobforce.services.parse import parse_html

    html = _read("netapp_job.html")
    result = parse_html(html, _NETAPP_URL)
    assert result["description"] is not None
    assert "Software Defined Storage" in result["description"]
