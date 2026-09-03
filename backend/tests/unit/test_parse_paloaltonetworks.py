"""Unit tests for the Palo Alto Networks (jobs.paloaltonetworks.com) adapter —
a section-based CMS template. The page has two headings before the real job
title: a marketing hero `<h1 class="section26__heading">` ("Revolutionizing
protection.") and a tagline `<h2>`; the real title lives further down in
`h2.section30__job-title` — the generic adapter's bare "h1" selector grabs
the hero tagline instead. There's no `og:site_name`/company element on this
template (this domain only ever serves Palo Alto Networks postings, so
company_name is a fixed value). location lives in a
`span.section30__job-info-location` that the generic adapter's
`[data-location], .job-location, .location` selectors don't match, so it
comes back null. description: the generic adapter's `[class*="description"]`
selector matches the outer `<section class="job-description ...">` wrapper
(which also contains the title, location, Ref ID, Apply button, and "Current
Employees" boilerplate) instead of the inner `.ats-description` div that
holds just the real job body — so description needs to point at
`.ats-description` directly.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_PALOALTONETWORKS_URL = "https://jobs.paloaltonetworks.com/en/job/santa-clara/sr-staff-software-engineer/47263/99699014768"


def test_parse_html_paloaltonetworks_title_overrides_hero_heading() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paloaltonetworks_job.html")
    result = parse_html(html, _PALOALTONETWORKS_URL)
    assert result["title"] == "Sr Staff Software Engineer"


def test_parse_html_paloaltonetworks_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paloaltonetworks_job.html")
    result = parse_html(html, _PALOALTONETWORKS_URL)
    assert result["company_name"] == "Palo Alto Networks"


def test_parse_html_paloaltonetworks_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paloaltonetworks_job.html")
    result = parse_html(html, _PALOALTONETWORKS_URL)
    assert result["location"] == "Santa Clara, California, United States of America"


def test_parse_html_paloaltonetworks_description_excludes_boilerplate() -> None:
    from jobforce.services.parse import parse_html

    html = _read("paloaltonetworks_job.html")
    result = parse_html(html, _PALOALTONETWORKS_URL)
    assert result["description"] is not None
    assert "AI-Native Cloud FinOps Engineer" in result["description"]
    # The outer wrapper's boilerplate (apply link, save-job button, ref id)
    # must not leak into the description once we point at .ats-description.
    assert "Save Job" not in result["description"]
    assert "Ref ID" not in result["description"]
