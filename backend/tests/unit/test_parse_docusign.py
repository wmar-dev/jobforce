"""Unit tests for the Docusign (careers.docusign.com/careers-home/jobs/<id>)
site adapter — title and description already extract fine via the generic
adapter; the site's own og:site_name meta is buggy and echoes the full "<title>
in <location> | careers-home" page title instead of "Docusign".
"#job-location" only shows one arbitrary location from a multi-location
posting, so location comes from "#header-locations" instead, which carries the
full list.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


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
