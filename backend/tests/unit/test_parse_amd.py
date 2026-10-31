"""Unit tests for the AMD (careers.amd.com) adapter — a Jibe-hosted Angular
board whose `og:site_name` is the full "<title> in <city> | Advanced Micro
Devices, Inc" page title (so the generic company fallback is junk), with no
`.location` element and a `job-description-container` holding untranslated
i18n keys. The `<script type="application/ld+json">` JobPosting block has
the real location and full description.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_AMD_URL = "https://careers.amd.com/careers-home/jobs/86514"


def test_parse_html_amd_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("amd_job.html")
    result = parse_html(html, _AMD_URL)
    assert result["company_name"] == "AMD"


def test_parse_html_amd_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("amd_job.html")
    result = parse_html(html, _AMD_URL)
    assert result["location"] == "San Jose, California"


def test_parse_html_amd_location_skips_unavailable_placeholder() -> None:
    from jobforce.services.parse import parse_html

    html = _read("amd_job.html").replace(
        '"addressLocality": "San Jose"', '"addressLocality": "UNAVAILABLE"'
    )
    result = parse_html(html, _AMD_URL)
    assert result["location"] == "California"


def test_parse_html_amd_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("amd_job.html")
    result = parse_html(html, _AMD_URL)
    assert result["description"] is not None
    assert "outsized impact" in result["description"]
    assert "JOB_DESCRIPTION.SHARE.HTML" not in result["description"]
