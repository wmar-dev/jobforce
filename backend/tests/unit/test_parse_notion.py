"""Unit tests for the Notion (*.notion.site/<page-id>) site adapter.

Fixture: notion_paradedb_job.html — ParadeDB Distributed Systems Engineer
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_NOTION_URL = "https://paradedb.notion.site/Distributed-Systems-Engineer-Postgres-Platform-1a5ea4ce9deb80aeb0ddd5cbbd10f654"


def test_parse_html_notion_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["title"] == "Distributed Systems Engineer — Postgres Platform"


def test_parse_html_notion_company_from_breadcrumb() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["company_name"] == "ParadeDB"


def test_parse_html_notion_location_from_property() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["location"] == "Remote, San Francisco"


def test_parse_html_notion_role_type_full_time() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["role_type"] == "full-time"


def test_parse_html_notion_description_non_null() -> None:
    from jobforce.services.parse import parse_html

    html = _read("notion_paradedb_job.html")
    result = parse_html(html, _NOTION_URL)
    assert result["description"] is not None
    assert "ParadeDB" in result["description"]
    assert "Postgres" in result["description"]


def test_match_adapter_notion_site_suffix() -> None:
    from jobforce.services.parse import SITE_ADAPTERS, _match_adapter

    assert "notion.site" in SITE_ADAPTERS
    assert _match_adapter("paradedb.notion.site") is SITE_ADAPTERS["notion.site"]
