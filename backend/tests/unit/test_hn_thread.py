"""Unit tests for jobforce.cli.hn_thread."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

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


_PIPE_THREAD = """<html><body>
<table class="comment-tree">
  <tr class="athing comtr" id="33333">
    <td><table><tr>
      <td class="ind" indent="0"><img src="s.gif" height="1" width="0"></td>
      <td class="default">
        <div class="comment"><div class="commtext c00">Acme | Staff Software Engineer | \
San Francisco, CA | Full-time<p>We build rockets.</p></div></div>
      </td>
    </tr></table></td>
  </tr>
  <tr class="athing comtr" id="44444">
    <td><table><tr>
      <td class="ind" indent="1"><img src="s.gif" height="1" width="40"></td>
      <td class="default">
        <div class="comment"><div class="commtext c00">A reply | Not a job | Nowhere</div></div>
      </td>
    </tr></table></td>
  </tr>
  <tr class="athing comtr" id="55555">
    <td><table><tr>
      <td class="ind" indent="0"><img src="s.gif" height="1" width="0"></td>
      <td class="default">
        <div class="comment"><div class="commtext c00 cdd">[dead]</div></div>
      </td>
    </tr></table></td>
  </tr>
</table>
</body></html>"""


# ---------------------------------------------------------------------------
# --details: parse every top-level comment from the thread page itself
# ---------------------------------------------------------------------------


def test_hn_thread_details_parses_pipe_header() -> None:
    from jobforce.cli.hn_thread import _extract_comment_details

    records = _extract_comment_details(_PIPE_THREAD)

    assert len(records) == 1  # reply and dead comment excluded
    rec = records[0]
    assert rec["source_url"] == "https://news.ycombinator.com/item?id=33333"
    assert rec["company_name"] == "Acme"
    assert rec["title"] == "Staff Software Engineer"
    assert rec["location"] == "San Francisco, CA"
    assert rec["role_type"] == "full-time"
    assert "We build rockets." in rec["description"]
    assert rec["first_line"].startswith("Acme | Staff Software Engineer")


def test_hn_thread_details_snapshot_reparses_identically() -> None:
    from jobforce.cli.hn_thread import _extract_comment_details
    from jobforce.services.parse import parse_html

    for rec in _extract_comment_details(_read("hn_thread.html")):
        reparsed = parse_html(rec["html"], rec["source_url"])
        for field in ("company_name", "title", "location", "role_type", "description"):
            assert reparsed.get(field) == rec.get(field)


def test_hn_thread_details_matches_comment_urls_on_fixture() -> None:
    from jobforce.cli.hn_thread import _extract_comment_details, _extract_comment_urls

    html = _read("hn_thread.html")
    records = _extract_comment_details(html)

    assert [r["source_url"] for r in records] == _extract_comment_urls(html, _BASE_URL)
    assert any(r["title"] for r in records)


# ---------------------------------------------------------------------------
# Pagination: follow "More" links
# ---------------------------------------------------------------------------


def test_hn_thread_follows_more_links(monkeypatch: Any) -> None:
    import jobforce.cli.hn_thread as mod

    pages = {
        _BASE_URL: '<a class="morelink" href="item?id=48357725&amp;p=2">More</a>',
        "https://news.ycombinator.com/item?id=48357725&p=2": "<html>last page</html>",
    }
    fetched: list[str] = []

    def fake_fetch(url: str) -> str:
        fetched.append(url)
        return pages[url]

    monkeypatch.setattr(mod, "_fetch_thread_html", fake_fetch)

    result = mod._fetch_thread_pages(_BASE_URL)

    assert fetched == list(pages)
    assert len(result) == 2


# ---------------------------------------------------------------------------
# --ingest: write records straight to the DB, skipping incomplete ones
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_hn_thread_ingest_records(db_engine: Any, tmp_path: Any) -> None:
    from sqlalchemy import select

    from jobforce.cli.hn_thread import _extract_comment_details, _ingest_with_factory
    from jobforce.db.engine import build_session_factory
    from jobforce.db.models import JobListing

    factory = build_session_factory(db_engine)
    records = _extract_comment_details(_PIPE_THREAD)
    records.append({"source_url": "https://news.ycombinator.com/item?id=66666", "title": None})

    results = await _ingest_with_factory(records, factory, pages_dir=str(tmp_path))

    assert results[0]["duplicate"] is False
    assert results[0]["title"] == "Staff Software Engineer"
    assert results[1]["skipped"] == "missing company_name or title"

    again = await _ingest_with_factory(records[:1], factory, pages_dir=str(tmp_path))
    assert again[0]["duplicate"] is True

    async with factory() as session:
        jobs = (await session.execute(select(JobListing))).scalars().all()
    assert [j.source_url for j in jobs] == ["https://news.ycombinator.com/item?id=33333"]
