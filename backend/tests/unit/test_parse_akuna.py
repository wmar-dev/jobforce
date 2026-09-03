"""Unit tests for the Akuna Capital (akunacapital.com) adapter — a WordPress
careers site backed by Greenhouse job data. title/company_name/description
already resolve correctly via the generic adapter (h1, og:site_name, and a
".job-description"-suffixed class all match), but location comes back null
(no ".location"/"[data-location]" element — the rendered location text sits
in an unclassed `<span>` inside a `<p class="sub">`), and role_type is
wrong: the generic body-text scan matches the standalone word "Intern" in
unrelated boilerplate ("...take a look at our Entry Level and Intern
positions") and reports "internship" even though the role is full-time.
Both fields are pulled instead from the `<script type="application/ld+json">`
JobPosting block the page also embeds (same pattern as the Box/Workable
adapters), which is authoritative and unaffected by boilerplate text
elsewhere on the page.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_AKUNA_URL = "https://akunacapital.com/careers/job/7974805/platform-engineer/"


def test_parse_html_akuna_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("akuna_job.html")
    result = parse_html(html, _AKUNA_URL)
    assert result["location"] == "Remote"


def test_parse_html_akuna_role_type() -> None:
    from jobforce.services.parse import parse_html

    html = _read("akuna_job.html")
    result = parse_html(html, _AKUNA_URL)
    assert result["role_type"] == "full-time"
