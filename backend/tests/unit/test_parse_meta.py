"""Unit tests for the Meta careers (metacareers.com) adapter — a React SPA with
no plain-text company/location/description elements or og:site_name meta tag;
all real job data lives in a schema.org JobPosting JSON-LD <script> block
(same pattern as the Dropbox/Workable adapters). Not a hydration race: the
raw HTML scout_fetch captures already contains this fully-populated JSON-LD
block by the time the bare "h1, main h2" wait resolves — the generic
adapter simply has no selector that finds it.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_META_URL = "https://www.metacareers.com/profile/job_details/2342974003201767"


def test_parse_html_meta_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("meta_job.html")
    result = parse_html(html, _META_URL)
    assert result["company_name"] == "Meta"


def test_parse_html_meta_location_joins_multiple_places() -> None:
    from jobforce.services.parse import parse_html

    html = _read("meta_job.html")
    result = parse_html(html, _META_URL)
    assert result["location"] == "Bellevue, WA; Menlo Park, CA"


def test_parse_html_meta_description_includes_responsibilities_and_qualifications() -> None:
    from jobforce.services.parse import parse_html

    html = _read("meta_job.html")
    result = parse_html(html, _META_URL)
    assert result["description"] is not None
    assert "Meta is seeking a Software Engineer" in result["description"]
    assert "Define and drive the long-term technical vision" in result["description"]
    assert "Bachelor's degree in Computer Science" in result["description"]


def test_parse_html_meta_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("meta_job.html")
    result = parse_html(html, _META_URL)
    assert result["role_type"] == "full-time"
