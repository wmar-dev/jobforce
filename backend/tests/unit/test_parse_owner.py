"""Unit tests for the Owner (owner.com) adapter — Webflow careers page at
/careers/role?=<uuid>; job fields are rendered into elements tagged with
data-role-* attributes (title, location, type, opening/html/additional body).
"""

from __future__ import annotations

from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_OWNER_BACKEND_URL = "https://www.owner.com/careers/role?=0b373b8f-ca11-4a4a-ad68-76ffd79a35d6"
_OWNER_FULLSTACK_URL = "https://www.owner.com/careers/role?=bae9c3e1-7f5f-4ea1-8ee3-0856a73165d3"

_CASES = [
    ("owner_job.html", _OWNER_BACKEND_URL, "Senior Software Engineer, Backend", "Remote"),
    (
        "owner_fullstack_job.html",
        _OWNER_FULLSTACK_URL,
        "Staff Software Engineer, Full-Stack",
        "Remote - United States or Canada",
    ),
]


@pytest.mark.parametrize(
    ("fixture", "url", "title", "location"), _CASES, ids=["backend", "fullstack"]
)
def test_parse_html_owner_company(fixture: str, url: str, title: str, location: str) -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read(fixture), url)
    assert result["company_name"] == "Owner"


@pytest.mark.parametrize(
    ("fixture", "url", "title", "location"), _CASES, ids=["backend", "fullstack"]
)
def test_parse_html_owner_location(fixture: str, url: str, title: str, location: str) -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read(fixture), url)
    assert result["location"] == location


@pytest.mark.parametrize(
    ("fixture", "url", "title", "location"), _CASES, ids=["backend", "fullstack"]
)
def test_parse_html_owner_description_non_null(
    fixture: str, url: str, title: str, location: str
) -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read(fixture), url)
    assert result["description"] is not None
    assert "AI-native system local business owners use" in result["description"]
    assert "Compensation and benefits" in result["description"]
