"""Unit tests for the HN (news.ycombinator.com) site adapter in parse.py."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"

_HN_URL = "https://news.ycombinator.com/item?id=48408037"
_HN_URL_PROSE = "https://news.ycombinator.com/item?id=48404934"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# T005: pipe-delimited comment extracts all structured fields
# ---------------------------------------------------------------------------


def test_hn_pipe_comment_extracts_fields() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("hn_comment_pipe.html"), _HN_URL)

    assert result["company_name"] == "Climate Friendly"
    assert result["title"] == "Senior Data Engineer"
    assert result["location"] is not None
    assert "Sydney" in result["location"]
    assert result["role_type"] == "full-time"
    assert result["description"] is not None
    assert len(result["description"]) > 10


# ---------------------------------------------------------------------------
# T006: prose comment — company non-null, title null, description is markdown
# ---------------------------------------------------------------------------


def test_hn_prose_comment_extracts_company() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("hn_comment_prose.html"), _HN_URL_PROSE)

    assert result["company_name"] is not None
    assert len(result["company_name"]) > 0
    assert result["title"] is None
    assert result["description"] is not None
    assert len(result["description"]) > 10


# ---------------------------------------------------------------------------
# T007: role_type detection from pipe tokens
# ---------------------------------------------------------------------------


def test_hn_pipe_role_type_detection() -> None:
    from jobforce.services.parse import parse_html

    result = parse_html(_read("hn_comment_pipe.html"), _HN_URL)

    assert result["role_type"] == "full-time"


# ---------------------------------------------------------------------------
# T008: fallback when no pipe in first line
# ---------------------------------------------------------------------------


def test_hn_pipe_missing_pipe_fallback() -> None:
    from jobforce.services.parse import parse_html

    # Minimal HN single-comment HTML with prose first line
    html = """<html><body>
    <table class="fatitem">
      <tr class="athing" id="99999">
        <td class="default">
          <div class="comment">
            <div class="commtext c00">Acme Corp is looking for engineers.<p>More details here.</div>
          </div>
        </td>
      </tr>
    </table>
    </body></html>"""
    url = "https://news.ycombinator.com/item?id=99999"

    result = parse_html(html, url)

    assert result["title"] is None
    assert result["company_name"] is not None
    # company_name should be the first word/token from the first line
    assert "Acme" in result["company_name"]
