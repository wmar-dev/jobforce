"""Unit tests for the Dropbox (dropbox.jobs/en/jobs/<id>/<slug>) site adapter —
company_name and location come from the page's own "#js-job-posting" schema.org
JobPosting JSON-LD block (same pattern as the Workable adapter), since the
generic adapter's og:site_name only yields the generic "Dropbox Careers" and
there's no plain-text location element.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_DROPBOX_URL = "https://www.dropbox.jobs/en/jobs/8006972/principal-software-engineer-core-sharing-collaboration/"


def test_parse_html_dropbox_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("dropbox_job.html")
    result = parse_html(html, _DROPBOX_URL)
    assert result["company_name"] == "Dropbox"


def test_parse_html_dropbox_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("dropbox_job.html")
    result = parse_html(html, _DROPBOX_URL)
    assert result["location"] == "Remote - US: All locations"


def test_parse_html_dropbox_description_from_jsonld() -> None:
    """The generic adapter finds no plain-text description container on this
    React-rendered page; description must come from the JSON-LD block."""
    from jobforce.services.parse import parse_html

    html = _read("dropbox_job.html")
    result = parse_html(html, _DROPBOX_URL)
    assert result["description"] is not None
    assert "Principal Engineer at Dropbox" in result["description"]
