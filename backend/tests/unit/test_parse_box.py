"""Unit tests for the Box (careers.box.com) adapter — the generic adapter's
`.location`/`[class*="description"]` selectors don't match this page's
markup (location lives in a `<ul class="job-meta">` link, description in an
`<article class="cms-content">` with no "description" in its class name),
so both come back null. All real job data is also mirrored in a
`<script type="application/ld+json">` JobPosting block, which is the
cleanest place to pull location and description from (title/company_name
already resolve correctly via the generic adapter's `h1` / `og:site_name`
fallbacks, so they're left alone here).
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BOX_URL = "https://careers.box.com/en/jobs/8133229/engineering-manager-ii-agent-runtime/"


def test_parse_html_box_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("box_job.html")
    result = parse_html(html, _BOX_URL)
    assert result["location"] == "Redwood City, California, United States"


def test_parse_html_box_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("box_job.html")
    result = parse_html(html, _BOX_URL)
    assert result["description"] is not None
    assert "Agent Runtime team is a platform team" in result["description"]
