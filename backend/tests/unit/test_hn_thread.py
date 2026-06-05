"""Unit tests for jobforce.cli.hn_thread."""

from __future__ import annotations

from pathlib import Path

FIXTURES = Path(__file__).parent.parent / "fixtures"

_BASE_URL = "https://news.ycombinator.com/item?id=48357725"


def _read(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# T018: thread fixture produces a non-empty list of comment URLs
# ---------------------------------------------------------------------------


def test_hn_thread_extracts_comment_urls() -> None:
    from jobforce.cli.hn_thread import _extract_comment_urls

    html = _read("hn_thread.html")
    urls = _extract_comment_urls(html, _BASE_URL)

    assert isinstance(urls, list)
    assert len(urls) > 0
    for url in urls:
        assert url.startswith("https://news.ycombinator.com/item?id=")


# ---------------------------------------------------------------------------
# T019: dead comments (cdd class) are excluded from results
# ---------------------------------------------------------------------------


def test_hn_thread_skips_dead_comments() -> None:
    from jobforce.cli.hn_thread import _extract_comment_urls

    html = """<html><body>
    <table class="comment-tree">
      <tr class="athing comtr" id="11111">
        <td><table><tr>
          <td class="ind" indent="0"><img src="s.gif" height="1" width="0"></td>
          <td class="default">
            <div class="comment"><div class="commtext c00">Live job post</div></div>
          </td>
        </tr></table></td>
      </tr>
      <tr class="athing comtr" id="22222">
        <td><table><tr>
          <td class="ind" indent="0"><img src="s.gif" height="1" width="0"></td>
          <td class="default">
            <div class="comment"><div class="commtext c00 cdd">[dead]</div></div>
          </td>
        </tr></table></td>
      </tr>
    </table>
    </body></html>"""

    urls = _extract_comment_urls(html, _BASE_URL)

    assert "https://news.ycombinator.com/item?id=11111" in urls
    assert "https://news.ycombinator.com/item?id=22222" not in urls
