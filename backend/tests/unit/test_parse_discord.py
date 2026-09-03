"""Unit tests for the Discord (discord.com/jobs/<id>) site adapter."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_DISCORD_URL = "https://discord.com/jobs/8136321002"


def test_parse_html_discord_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["title"] == "Senior Software Engineer - Platform Infrastructure"


def test_parse_html_discord_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["company_name"] == "Discord"


def test_parse_html_discord_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["location"] == "San Francisco Bay Area"


def test_parse_html_discord_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("discord_job.html")
    result = parse_html(html, _DISCORD_URL)
    assert result["description"] is not None
    assert "distributed systems" in result["description"]
