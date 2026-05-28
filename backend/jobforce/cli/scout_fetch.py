"""CLI tool: fetch a job page headlessly and parse it into structured JSON."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from urllib.parse import urlparse

from jobforce.services.parse import parse_html

_TIMEOUT_MS = 30_000


async def _fetch_and_parse(url: str) -> dict:  # type: ignore[type-arg]
    from playwright.async_api import TimeoutError as PlaywrightTimeout
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        try:
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=_TIMEOUT_MS)
                await page.wait_for_selector("main h2", timeout=10_000)
            except PlaywrightTimeout:
                print(f"error: page load timed out after {_TIMEOUT_MS // 1000}s: {url}", file=sys.stderr)
                sys.exit(1)
            html = await page.evaluate("document.documentElement.outerHTML")
        finally:
            await browser.close()

    return parse_html(html, url)


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise argparse.ArgumentTypeError(f"Invalid URL: {url!r}")
    return url


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch and parse a job listing URL")
    parser.add_argument("--url", required=True, type=_validate_url, help="Job listing URL to fetch")
    args = parser.parse_args()

    result = asyncio.run(_fetch_and_parse(args.url))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
