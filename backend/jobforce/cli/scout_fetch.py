"""CLI tool: fetch a job page headlessly, parse it, and ingest into the database."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from urllib.parse import urlparse

from jobforce.services.parse import parse_html

_TIMEOUT_MS = 30_000


async def _fetch_html(url: str) -> str:
    from playwright.async_api import TimeoutError as PlaywrightTimeout
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        try:
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=_TIMEOUT_MS)
                await page.wait_for_selector("h1, main h2", timeout=10_000)
            except PlaywrightTimeout:
                print(
                    f"error: page load timed out after {_TIMEOUT_MS // 1000}s: {url}",
                    file=sys.stderr,
                )
                sys.exit(1)
            return str(await page.evaluate("document.documentElement.outerHTML"))
        finally:
            await browser.close()


async def _ingest(url: str, html: str, parsed: dict) -> dict:  # type: ignore[type-arg]
    from jobforce.config import load_config
    from jobforce.db.engine import build_engine, build_session_factory
    from jobforce.services.scout import IngestPayload, ingest_listing

    cfg = load_config()
    engine = build_engine(cfg.database.path)
    factory = build_session_factory(engine)
    try:
        async with factory() as session:
            payload = IngestPayload(
                source_url=url,
                html=html,
                title=parsed.get("title") or "",
                company_name=parsed.get("company_name") or "",
                location=parsed.get("location"),
                role_type=parsed.get("role_type"),
                description=parsed.get("description"),
            )
            return await ingest_listing(session, payload)
    finally:
        await engine.dispose()


async def _run(url: str, dry_run: bool) -> dict:  # type: ignore[type-arg]
    html = await _fetch_html(url)
    parsed = parse_html(html, url)
    if not parsed.get("company_name") or not parsed.get("title"):
        print(
            "error: page does not look like a job listing "
            f"(company_name={parsed.get('company_name')!r}, title={parsed.get('title')!r}). "
            "Provide a direct job listing URL, not a homepage or careers index.",
            file=sys.stderr,
        )
        sys.exit(1)
    if dry_run:
        return parsed
    result = await _ingest(url, html, parsed)
    return {**parsed, **result}


def _validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise argparse.ArgumentTypeError(f"Invalid URL: {url!r}")
    return url


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch, parse, and ingest a job listing URL")
    parser.add_argument("--url", required=True, type=_validate_url, help="Job listing URL to fetch")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse only, do not write to database"
    )
    args = parser.parse_args()

    result = asyncio.run(_run(args.url, args.dry_run))
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
