"""Unit tests for the Guidewire (guidewire.com/about/careers/jobs/<slug>) site
adapter — no <h1>; the page uses <h2> for the job title, so the generic adapter
falls back to the <title> tag and truncates at the first " - ", dropping
team-qualifier suffixes like "- Cloud Data Platform" from titles that
legitimately contain a hyphen. Location and description aren't exposed via any
plain element the generic adapter checks — its description fallback picks up
the site's footer boilerplate ("We do not accept bot-generated candidate
applications...") instead.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_GUIDEWIRE_URL = "https://www.guidewire.com/about/careers/jobs/senior-software-engineer---cloud-data-platform-jr_14462"


def test_parse_html_guidewire_title_full_not_truncated_at_hyphen() -> None:
    from jobforce.services.parse import parse_html

    html = _read("guidewire_job.html")
    result = parse_html(html, _GUIDEWIRE_URL)
    assert result["title"] == "Senior Software Engineer - Cloud Data Platform"


def test_parse_html_guidewire_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("guidewire_job.html")
    result = parse_html(html, _GUIDEWIRE_URL)
    assert result["location"] == "United States - San Mateo, CA"


def test_parse_html_guidewire_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("guidewire_job.html")
    result = parse_html(html, _GUIDEWIRE_URL)
    assert result["description"] is not None
    assert "machine learning lifecycle" in result["description"]
