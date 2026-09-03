"""Unit tests for the Block (block.xyz/careers/jobs/<id>) site adapter — the
site's own og:site_name meta is buggy and echoes the page title instead of
"Block", so the generic adapter's company_name fallback grabs the wrong text;
location and description need dedicated selectors too.
"""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


_BLOCK_URL = "https://block.xyz/careers/jobs/5243440008"


def test_parse_html_block_title_via_generic_h1() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["title"] == "Senior Machine Learning Engineer, Applied AI Quality"


def test_parse_html_block_company() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["company_name"] == "Block"


def test_parse_html_block_location() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["location"] == "Bay Area, CA, US"


def test_parse_html_block_description() -> None:
    from jobforce.services.parse import parse_html

    html = _read("block_job.html")
    result = parse_html(html, _BLOCK_URL)
    assert result["description"] is not None
    assert "Applied AI Quality team" in result["description"]
