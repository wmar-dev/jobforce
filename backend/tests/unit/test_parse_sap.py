"""Unit tests for the SAP (jobs.sap.com) site adapter — SuccessFactors/jobs2web
careers template. title and description already extract fine via the generic
adapter (h1 + a ".jobdescription" element matching the "description" class
substring selector); company_name isn't exposed anywhere the generic adapter
looks (no data-company/.company-name element, no og:site_name meta) but is
present as schema.org JobPosting microdata (<meta itemprop="hiringOrganization">).
location is worse than missing — the generic ".job-location" selector matches
a "Nearest Major Market" trailer paragraph embedded in the description body,
not the real location, so it needs to come from the ".jobGeoLocation" span
instead.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_SAP_URL = (
    "https://jobs.sap.com/job/Palo-Alto-Data-Science-Chief-Expert%2C-Finance-CA-94304/1430550933/"
)


def test_parse_html_sap_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sap_job.html")
    result = parse_html(html, _SAP_URL)
    assert result["company_name"] == "SAP"


def test_parse_html_sap_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sap_job.html")
    result = parse_html(html, _SAP_URL)
    assert result["location"] == "Palo Alto, CA, US, 94304"


def test_parse_html_sap_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("sap_job.html")
    result = parse_html(html, _SAP_URL)
    assert result["description"] is not None
    assert "context engine that makes AI enterprise ready" in result["description"]
