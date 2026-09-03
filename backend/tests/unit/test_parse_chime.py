"""Unit tests for the Chime (careers.chime.com/jobs/<id>/<slug>) site adapter —
title extracts fine via the generic adapter's <h1>; company_name, location, and
description need overrides. Location is the second of two <p> tags inside
".content-wrapper" (department, then location); description is the ".jobCopy"
container.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_CHIME_URL = "https://careers.chime.com/jobs/8569366002/senior-ai-ml-engineer"


def test_parse_html_chime_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert result["title"] == "Senior AI/ML Engineer"


def test_parse_html_chime_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert result["company_name"] == "Chime"


def test_parse_html_chime_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert (
        result["location"]
        == "Chicago, IL, USA; New York, NY, USA; San Francisco, CA, USA; Seattle, WA, USA"
    )


def test_parse_html_chime_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("chime_job.html")
    result = parse_html(html, _CHIME_URL)
    assert result["description"] is not None
    assert "Growth & Marketing AI" in result["description"]
