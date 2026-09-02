"""CLI tool: fetch a job page headlessly, parse it, and ingest into the database."""

from __future__ import annotations

import argparse
import asyncio
import html as html_module
import json
import sys
from urllib.parse import parse_qs, urlparse

from jobforce.services.parse import parse_html

_TIMEOUT_MS = 30_000


async def _fetch_nebius_greenhouse_html(url: str) -> str | None:
    """careers.nebius.com embeds the actual Greenhouse job description and
    apply flow in a cross-origin iframe that the wrapper page's own DOM never
    exposes — and unlike other Greenhouse-embedded sites, there's no direct
    job-boards.greenhouse.io fallback either (Greenhouse permanently 302s
    that URL back to this same wrapper for Nebius). Bypass rendering
    entirely and pull the job data from Greenhouse's public, unauthenticated
    Jobs API instead, then synthesize minimal HTML for parse_html to read.
    """
    import httpx

    parsed = urlparse(url)
    if "careers.nebius.com" not in (parsed.hostname or ""):
        return None
    gh_jid_values = parse_qs(parsed.query).get("gh_jid") or []
    if not gh_jid_values:
        return None
    gh_jid = gh_jid_values[0]
    api_url = f"https://boards-api.greenhouse.io/v1/boards/nebius/jobs/{gh_jid}?content=true"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(api_url)
    if resp.status_code != 200:
        return None
    data = resp.json()
    title = html_module.escape((data.get("title") or "").strip())
    location = html_module.escape((data.get("location") or {}).get("name") or "")
    description_html = html_module.unescape(data.get("content") or "")
    return (
        f"<!doctype html><html><head><title>{title} | Nebius</title></head><body>"
        f'<h1 class="nebius-gh-title">{title}</h1>'
        f'<div class="nebius-gh-location">{location}</div>'
        f'<div class="nebius-gh-description">{description_html}</div>'
        "</body></html>"
    )


# Hosts whose job content hydrates in client-side after the initial DOM
# marker (h1/h2) is already attached, so a bare "h1, main h2" wait resolves
# before the real title/location/description are present. Maps a hostname
# substring to a JS expression that's truthy once the real content has
# rendered — scout_fetch polls it (via wait_for_function) before capturing.
_HYDRATION_WAIT_CONDITIONS: dict[str, str] = {
    # apply.workable.com renders an empty <h1 data-ui="job-title"> shell
    # immediately on domcontentloaded; the JSON-LD block and real title only
    # appear once client-side hydration finishes.
    "apply.workable.com": (
        "document.querySelector('h1[data-ui=\"job-title\"]')?.textContent.trim().length > 0"
    ),
    # jobs.twilio.com's <h1> is a static "Single Position" shell; the real
    # title/description only render after the Eightfold SPA hydrates and
    # fetches the job data client-side.
    "jobs.twilio.com": (
        "document.querySelector('h2[class*=\"position-title\"]')?.textContent.trim().length > 0"
    ),
    # careers.chime.com's <h1>/title render immediately, but the ".jobCopy"
    # description div is present-but-empty until the SPA hydrates and fills
    # in the job body client-side.
    "careers.chime.com": "document.querySelector('.jobCopy')?.textContent.trim().length > 0",
    # coinbase.com/careers is a heavy client-rendered SPA; the generic wait
    # can resolve before the real job content (".content-intro") has
    # hydrated in, so wait on it directly to avoid an intermittent race.
    "coinbase.com": "document.querySelector('.content-intro')?.textContent.trim().length > 0",
    # careers.docusign.com's <h1>/title render immediately, but the
    # "#header-locations" element is added to the DOM later once client-side
    # hydration finishes.
    "careers.docusign.com": (
        "document.querySelector('#header-locations')?.textContent.trim().length > 0"
    ),
}


async def _fetch_html(url: str) -> str:
    nebius_html = await _fetch_nebius_greenhouse_html(url)
    if nebius_html is not None:
        return nebius_html

    from playwright.async_api import TimeoutError as PlaywrightTimeout
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        try:
            page = await browser.new_page()
            try:
                await page.goto(url, wait_until="domcontentloaded", timeout=_TIMEOUT_MS)
            except PlaywrightTimeout:
                print(
                    f"error: page load timed out after {_TIMEOUT_MS // 1000}s: {url}",
                    file=sys.stderr,
                )
                sys.exit(1)
            # Workday tenants render a sitewide h1 (e.g. "Careers at Acme") immediately
            # while the actual job content hydrates later via XHR, so a bare
            # "h1, main h2" wait resolves before the job title/location/description
            # are in the DOM. Wait on the job-specific marker for those hosts instead.
            hostname = urlparse(url).hostname or ""
            is_workday = "myworkdayjobs.com" in hostname
            hydration_condition = next(
                (cond for host, cond in _HYDRATION_WAIT_CONDITIONS.items() if host in hostname),
                None,
            )
            wait_selector = (
                "[data-automation-id='jobPostingHeader'],"
                " [data-automation-id='job-posting-details']"
                if is_workday
                else "h1, main h2"
            )
            try:
                await page.wait_for_selector(wait_selector, timeout=10_000, state="attached")
                if hydration_condition is not None:
                    try:
                        await page.wait_for_function(hydration_condition, timeout=10_000)
                    except PlaywrightTimeout:
                        pass
            except PlaywrightTimeout:
                # SPA pages without the expected marker (e.g. TikTok): wait for JS to hydrate content
                await page.wait_for_timeout(5_000)
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
