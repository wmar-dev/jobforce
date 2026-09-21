"""Unit tests for the ByteDance (joinbytedance.com) adapter — the company's
own custom careers site has no og:site_name/footer to derive company_name
from, and location is a label/value pair of sibling <p> tags.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BYTEDANCE_URL = "https://joinbytedance.com/search/7434029939458017590"


def test_parse_html_joinbytedance_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("joinbytedance_job.html")
    result = parse_html(html, _BYTEDANCE_URL)
    assert result["title"] == "Senior Software Engineer- Metadata Storage"


def test_parse_html_joinbytedance_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("joinbytedance_job.html")
    result = parse_html(html, _BYTEDANCE_URL)
    assert result["company_name"] == "ByteDance"


def test_parse_html_joinbytedance_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("joinbytedance_job.html")
    result = parse_html(html, _BYTEDANCE_URL)
    assert result["location"] == "San Jose"


def test_parse_html_joinbytedance_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("joinbytedance_job.html")
    result = parse_html(html, _BYTEDANCE_URL)
    assert result["description"] is not None
    assert "metadata services" in result["description"]
