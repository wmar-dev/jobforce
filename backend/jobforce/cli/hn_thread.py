"""CLI: fetch an HN 'Who's Hiring' thread and emit comment URLs as JSON.

Usage:
    python -m jobforce.cli.hn_thread <thread_url>

Output: JSON array of top-level, live comment URLs to stdout.
Errors: human-readable messages to stderr; exit code 1 on failure.
"""

from __future__ import annotations

import json
import sys
import urllib.request
from urllib.parse import urlparse

from bs4 import BeautifulSoup

_USER_AGENT = "Mozilla/5.0"
_HN_BASE = "https://news.ycombinator.com"


def _extract_comment_urls(html: str, base_url: str) -> list[str]:
    """Parse thread HTML and return top-level, non-dead comment URLs."""
    soup = BeautifulSoup(html, "lxml")
    urls: list[str] = []
    for row in soup.select("tr.athing.comtr"):
        # top-level only: indent cell has indent="0"
        ind = row.select_one("td.ind")
        if ind is None or ind.get("indent") != "0":
            continue
        # skip dead/flagged comments
        commtext = row.select_one(".commtext")
        if commtext is not None:
            classes: list[str] = commtext.get("class") or []  # type: ignore[assignment]
            if "cdd" in classes or "cdf" in classes:
                continue
        comment_id = row.get("id")
        if comment_id:
            urls.append(f"{_HN_BASE}/item?id={comment_id}")
    return urls


def _fetch_thread_html(url: str) -> str:
    """Fetch thread HTML via plain HTTP. Raises on non-200."""
    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} for {url}")
        return resp.read().decode("utf-8", errors="replace")  # type: ignore[no-any-return]


def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python -m jobforce.cli.hn_thread <thread_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    hostname = urlparse(url).hostname or ""
    if not hostname.endswith("news.ycombinator.com"):
        print(f"[hn_thread] error: not an HN URL: {url}", file=sys.stderr)
        sys.exit(1)

    print(f"[hn_thread] fetching {url}", file=sys.stderr)
    try:
        html = _fetch_thread_html(url)
    except Exception as exc:
        print(f"[hn_thread] error: {exc}", file=sys.stderr)
        sys.exit(1)

    comment_urls = _extract_comment_urls(html, url)
    print(f"[hn_thread] found {len(comment_urls)} top-level comments", file=sys.stderr)
    print(json.dumps(comment_urls))


if __name__ == "__main__":
    main()
