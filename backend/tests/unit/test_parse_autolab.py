"""Unit tests for the Autolab (autolab.ai) adapter — single-page careers site;
each role is a <details id="slug"> block and the URL fragment selects the role.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BASE = "https://www.autolab.ai/careers.html"
_POST = _BASE + "#post-training-ml-engineer"
_HARNESS = _BASE + "#harness-and-agents-engineer"


def test_parse_html_autolab_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("autolab_job.html")
    assert parse_html(html, _POST)["title"] == "Post-training ML Engineer"
    assert parse_html(html, _HARNESS)["title"] == "Harness & Agents Engineer"


def test_parse_html_autolab_company() -> None:
    from jobforce.services.parse import parse_html

    assert parse_html(_read("autolab_job.html"), _POST)["company_name"] == "Autolab"


def test_parse_html_autolab_location() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("autolab_job.html"), _POST)
    assert result["location"] == "San Francisco, California"


def test_parse_html_autolab_description_is_role_specific() -> None:
    from jobforce.services.parse import parse_html

    html = _read("autolab_job.html")
    post = parse_html(html, _POST)["description"]
    assert post is not None
    assert "reward design" in post
    assert "agent harness" not in post
    harness = parse_html(html, _HARNESS)["description"]
    assert harness is not None
    assert "agent harness" in harness
