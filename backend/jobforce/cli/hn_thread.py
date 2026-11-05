"""CLI: fetch an HN 'Who's Hiring' thread and extract or ingest its job comments.

Usage:
    python -m jobforce.cli.hn_thread <thread_url>             # comment URLs
    python -m jobforce.cli.hn_thread <thread_url> --details   # parsed comments
    python -m jobforce.cli.hn_thread --ingest <records.json>  # ingest records

Default output: JSON array of top-level, live comment URLs to stdout.

--details: JSON array of parsed records, one per top-level live comment, with
the same fields scout_fetch produces for a single comment page (source_url,
company_name, title, location, role_type, description) plus first_line and
html. Every comment is read from the thread page itself (following "More"
pagination links), so no per-comment requests are made. html is a
single-comment snapshot that parse_html understands, so
POST /api/jobs/{id}/reparse keeps working on ingested jobs.

--ingest: reads a JSON array of --details records (typically filtered first)
and ingests each one. Records missing company_name or title are skipped.
Prints one JSON summary per record.

Errors: human-readable messages to stderr; exit code 1 on failure.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from jobforce.services.parse import parse_html
from jobforce.services.parse._hn import _hn_first_line

_USER_AGENT = "Mozilla/5.0"
_HN_BASE = "https://news.ycombinator.com"
_MAX_PAGES = 20


def _top_level_live_rows(soup: BeautifulSoup) -> list[tuple[str, Tag]]:
    """Return (comment_id, commtext) for each top-level, non-dead comment."""
    rows: list[tuple[str, Tag]] = []
    for row in soup.select("tr.athing.comtr"):
        # top-level only: indent cell has indent="0"
        ind = row.select_one("td.ind")
        if ind is None or ind.get("indent") != "0":
            continue
        commtext = row.select_one(".commtext")
        if commtext is None:
            continue
        # skip dead/flagged comments
        classes: list[str] = commtext.get("class") or []  # type: ignore[assignment]
        if "cdd" in classes or "cdf" in classes:
            continue
        comment_id = row.get("id")
        if comment_id:
            rows.append((str(comment_id), commtext))
    return rows


def _extract_comment_urls(html: str, base_url: str) -> list[str]:
    """Parse thread HTML and return top-level, non-dead comment URLs."""
    soup = BeautifulSoup(html, "lxml")
    return [f"{_HN_BASE}/item?id={cid}" for cid, _ in _top_level_live_rows(soup)]


def _comment_snapshot(commtext: Tag) -> str:
    """Wrap a thread commtext in the single-comment page layout _parse_hn expects."""
    return (
        '<html><body><table class="fatitem"><tr class="athing"><td class="default">'
        f'<div class="comment">{commtext}</div>'
        "</td></tr></table></body></html>"
    )


def _extract_comment_details(html: str) -> list[dict[str, Any]]:
    """Parse thread HTML into one ingest-ready record per top-level live comment."""
    soup = BeautifulSoup(html, "lxml")
    records: list[dict[str, Any]] = []
    for cid, commtext in _top_level_live_rows(soup):
        url = f"{_HN_BASE}/item?id={cid}"
        snapshot = _comment_snapshot(commtext)
        parsed = parse_html(snapshot, url)
        records.append({**parsed, "first_line": _hn_first_line(commtext), "html": snapshot})
    return records


def _next_page_url(html: str, url: str) -> str | None:
    """Return the absolute URL of the thread's "More" page link, if any."""
    soup = BeautifulSoup(html, "lxml")
    link = soup.select_one("a.morelink")
    href = link.get("href") if link is not None else None
    return urljoin(url, str(href)) if href else None


def _fetch_thread_html(url: str) -> str:
    """Fetch thread HTML via plain HTTP. Raises on non-200."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return resp.read().decode("utf-8", errors="replace")  # type: ignore[no-any-return]


def _fetch_thread_pages(url: str) -> list[str]:
    """Fetch the thread page and every "More" continuation page."""
    pages: list[str] = []
    next_url: str | None = url
    while next_url and len(pages) < _MAX_PAGES:
        html = _fetch_thread_html(next_url)
        pages.append(html)
        next_url = _next_page_url(html, next_url)
    return pages


async def _ingest_with_factory(
    records: list[dict[str, Any]],
    factory: async_sessionmaker[AsyncSession],
    **ingest_kwargs: Any,
) -> list[dict[str, Any]]:
    """Ingest each record in its own session; skip records missing required fields."""
    from jobforce.services.scout import IngestPayload, ingest_listing

    results: list[dict[str, Any]] = []
    for rec in records:
        summary = {
            "source_url": rec.get("source_url"),
            "company_name": rec.get("company_name"),
            "title": rec.get("title"),
            "location": rec.get("location"),
        }
        if not rec.get("source_url") or not rec.get("company_name") or not rec.get("title"):
            results.append({**summary, "skipped": "missing company_name or title"})
            continue
        payload = IngestPayload(
            source_url=rec["source_url"],
            html=rec.get("html") or "",
            title=rec["title"],
            company_name=rec["company_name"],
            location=rec.get("location"),
            role_type=rec.get("role_type"),
            description=rec.get("description"),
        )
        async with factory() as session:
            result = await ingest_listing(session, payload, **ingest_kwargs)
        results.append({**summary, "id": result["id"], "duplicate": result["duplicate"]})
    return results


async def _ingest_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    from jobforce.config import load_config
    from jobforce.db.engine import build_engine, build_session_factory

    cfg = load_config()
    engine = build_engine(cfg.database.path)
    try:
        return await _ingest_with_factory(records, build_session_factory(engine))
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract or ingest HN Who's Hiring comments")
    parser.add_argument("thread_url", nargs="?", help="HN thread URL")
    parser.add_argument(
        "--details", action="store_true", help="Emit parsed records instead of comment URLs"
    )
    parser.add_argument("--ingest", metavar="FILE", help="Ingest a JSON array of --details records")
    args = parser.parse_args()

    if args.ingest:
        try:
            records = json.loads(Path(args.ingest).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"[hn_thread] error: cannot read {args.ingest}: {exc}", file=sys.stderr)
            sys.exit(1)
        if not isinstance(records, list):
            print("[hn_thread] error: --ingest file must hold a JSON array", file=sys.stderr)
            sys.exit(1)
        results = asyncio.run(_ingest_records(records))
        for r in results:
            print(json.dumps(r, ensure_ascii=False))
        return

    if not args.thread_url:
        parser.error("thread_url is required unless --ingest is given")

    url = args.thread_url
    hostname = urlparse(url).hostname or ""
    if not hostname.endswith("news.ycombinator.com"):
        print(f"[hn_thread] error: not an HN URL: {url}", file=sys.stderr)
        sys.exit(1)

    print(f"[hn_thread] fetching {url}", file=sys.stderr)
    try:
        pages = _fetch_thread_pages(url)
    except Exception as exc:
        print(f"[hn_thread] error: {exc}", file=sys.stderr)
        sys.exit(1)

    if args.details:
        details = [rec for html in pages for rec in _extract_comment_details(html)]
        print(f"[hn_thread] parsed {len(details)} top-level comments", file=sys.stderr)
        print(json.dumps(details, ensure_ascii=False))
        return

    comment_urls = [u for html in pages for u in _extract_comment_urls(html, url)]
    print(f"[hn_thread] found {len(comment_urls)} top-level comments", file=sys.stderr)
    print(json.dumps(comment_urls))


if __name__ == "__main__":
    main()
