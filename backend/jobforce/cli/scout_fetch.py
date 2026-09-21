"""CLI tool: fetch a job page headlessly, parse it, and ingest into the database."""

from __future__ import annotations

import argparse
import asyncio
import html as html_module
import json
import sys
from typing import Any
from urllib.parse import parse_qs, urlparse

from jobforce.services.parse import parse_html

_TIMEOUT_MS = 30_000


def _normalize_ashby_embed_url(url: str) -> str:
    """ashbyhq.com/careers?ashby_jid=<uuid> is Ashby's own marketing site, which
    embeds its job board in an <iframe title="Ashby Job Board">. scout_fetch's
    outerHTML capture only sees the top-level document, so it never sees the
    real job content (title/location/description all come back null/wrong,
    same root cause as the Nebius/CoreWeave cross-origin-iframe cases below —
    but simpler to fix here since the un-embedded page for the same posting
    already exists and already parses correctly via sites/ashby.py: rewrite to
    the canonical jobs.ashbyhq.com/Ashby/<jid> URL and let the normal fetch +
    parse flow run against that instead.
    """
    parsed = urlparse(url)
    hostname = (parsed.hostname or "").removeprefix("www.")
    if hostname != "ashbyhq.com":
        return url
    jid_values = parse_qs(parsed.query).get("ashby_jid") or []
    if not jid_values:
        return url
    return f"https://jobs.ashbyhq.com/Ashby/{jid_values[0]}"


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


async def _fetch_sentinelone_greenhouse_html(url: str) -> str | None:
    """sentinelone.com/jobs/?gh_jid=... embeds the actual Greenhouse job
    description and apply flow in a cross-origin iframe
    (job-boards.greenhouse.io/embed/job_app?for=sentinellabs&...) that the
    wrapper page's own DOM never exposes — title/company_name happen to come
    through fine (from the wrapper's own <title>/og:site_name), but
    location/description come back null/bogus. Same root cause and fix as
    careers.nebius.com / coreweave.com above: bypass rendering entirely and
    pull the job data from Greenhouse's public, unauthenticated Jobs API
    instead, using the "sentinellabs" board token discovered from the
    iframe's `for=` query param.
    """
    import httpx

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").removeprefix("www.")
    if hostname != "sentinelone.com":
        return None
    gh_jid_values = parse_qs(parsed.query).get("gh_jid") or []
    if not gh_jid_values:
        return None
    gh_jid = gh_jid_values[0]
    api_url = f"https://boards-api.greenhouse.io/v1/boards/sentinellabs/jobs/{gh_jid}?content=true"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(api_url)
    if resp.status_code != 200:
        return None
    data = resp.json()
    title = html_module.escape((data.get("title") or "").strip())
    location = html_module.escape((data.get("location") or {}).get("name") or "")
    description_html = html_module.unescape(data.get("content") or "")
    return (
        f"<!doctype html><html><head><title>{title} | SentinelOne</title></head><body>"
        f'<h1 class="sentinelone-gh-title">{title}</h1>'
        f'<div class="sentinelone-gh-location">{location}</div>'
        f'<div class="sentinelone-gh-description">{description_html}</div>'
        "</body></html>"
    )


async def _fetch_coreweave_greenhouse_html(url: str) -> str | None:
    """coreweave.com/careers/job embeds the actual Greenhouse job description
    and apply flow in a cross-origin iframe
    (job-boards.greenhouse.io/embed/job_app?...) that the wrapper page's own
    DOM never exposes — same root cause as careers.nebius.com above. Bypass
    rendering entirely and pull the job data from Greenhouse's public,
    unauthenticated Jobs API instead, then synthesize minimal HTML for
    parse_html to read.
    """
    import httpx

    parsed = urlparse(url)
    hostname = (parsed.hostname or "").removeprefix("www.")
    if hostname != "coreweave.com":
        return None
    gh_jid_values = parse_qs(parsed.query).get("gh_jid") or []
    if not gh_jid_values:
        return None
    gh_jid = gh_jid_values[0]
    api_url = f"https://boards-api.greenhouse.io/v1/boards/coreweave/jobs/{gh_jid}?content=true"
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(api_url)
    if resp.status_code != 200:
        return None
    data = resp.json()
    title = html_module.escape((data.get("title") or "").strip())
    location = html_module.escape((data.get("location") or {}).get("name") or "")
    description_html = html_module.unescape(data.get("content") or "")
    return (
        f"<!doctype html><html><head><title>{title} | CoreWeave</title></head><body>"
        f'<h1 class="coreweave-gh-title">{title}</h1>'
        f'<div class="coreweave-gh-location">{location}</div>'
        f'<div class="coreweave-gh-description">{description_html}</div>'
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
    # surgehq.ai/careers?id=... renders a static "Careers" <h1> shell for the
    # index list immediately; the actual job's h2.js-title only fills in once
    # the Webflow CMS list finishes hydrating and matches the ?id= param.
    "surgehq.ai": "document.querySelector('h2.js-title')?.textContent.trim().length > 0",
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
    # Phenom People boards (Yelp, Adobe) attach an empty <h1 class="job-title">
    # template shell immediately, satisfying the bare "h1, main h2" wait
    # before the client-side hydration that fills in the real title,
    # location, and description (and the page's JobPosting JSON-LD block)
    # has run — left job 3106's Adobe listing with everything but
    # company_name null on first crawl.
    "yelp.careers": "document.querySelector('h1.job-title')?.textContent.trim().length > 0",
    "careers.adobe.com": ("document.querySelector('h1.job-title')?.textContent.trim().length > 0"),
    # apply.careers.microsoft.com is the same Eightfold-powered ATS as
    # jobs.twilio.com: the static <h1> ("Single Position") attaches
    # immediately, satisfying the bare "h1, main h2" wait before the real
    # title/location/description hydrate into the <h2> and description
    # container below it.
    "apply.careers.microsoft.com": (
        "document.querySelector('h2[class*=\"position-title\"]')?.textContent.trim().length > 0"
    ),
    # Same Eightfold ATS as jobs.twilio.com / apply.careers.microsoft.com, on
    # tenants' own eightfold.ai subdomains (e.g. lockheedmartin.eightfold.ai).
    "eightfold.ai": (
        "document.querySelector('h2[class*=\"position-title\"]')?.textContent.trim().length > 0"
    ),
}

# Newer Eightfold tenants (e.g. lockheedmartin.eightfold.ai) render the job
# body behind a "Job Description" tab that doesn't fetch/render its content
# until clicked — unlike jobs.twilio.com's single-page layout, waiting for
# hydration alone leaves #job-description-container empty.
_TAB_CLICK_HOSTS: tuple[str, ...] = ("eightfold.ai",)


async def _extract_icims_frame_html(page: Any) -> str | None:
    """iCIMS always renders the real job content inside a same-origin
    <iframe src="*.icims.com/...?in_iframe=1">, even on the "canonical"
    (non-iframe) job URL — the wrapper page is just a branded "welcome" shell
    with nav chrome and no job content of its own, so capturing its
    outerHTML alone yields null location/description/role_type. The iframe
    is same-origin, so its contentDocument is reachable from the wrapper's
    JS context; merge its job container into the wrapper's own <head> (which
    carries a clean company og:site_name meta the iframe's own head lacks —
    the iframe's og:site_name is just the generic literal "careers").
    """
    result = await page.evaluate(
        """() => {
            const frame = document.querySelector('iframe[src*="icims.com"]');
            const fdoc = frame && frame.contentDocument;
            if (!fdoc) return null;
            const job = fdoc.querySelector('.iCIMS_JobContainer') || fdoc.body;
            if (!job) return null;
            return '<!doctype html><html><head>' + document.head.innerHTML +
                '</head><body>' + job.outerHTML + '</body></html>';
        }"""
    )
    return result if isinstance(result, str) else None


async def _wait_for_icims_and_extract(page: Any, hostname: str) -> str | None:
    if not hostname.endswith("icims.com"):
        return None
    from playwright.async_api import TimeoutError as PlaywrightTimeout

    try:
        await page.wait_for_function(
            "document.querySelector('iframe[src*=\"icims.com\"]')"
            "?.contentDocument?.querySelector('h1')"
            "?.textContent?.trim()?.length > 0",
            timeout=10_000,
        )
    except PlaywrightTimeout:
        pass
    return await _extract_icims_frame_html(page)


async def _click_eightfold_description_tab(page: Any, hostname: str) -> None:
    """Newer Eightfold tenants (e.g. lockheedmartin.eightfold.ai) render the
    job body behind a "Job Description" tab that doesn't fetch/render its
    content until clicked — unlike jobs.twilio.com's single-page layout,
    waiting for hydration alone leaves #job-description-container empty."""
    if not any(hostname.endswith(h) for h in _TAB_CLICK_HOSTS):
        return
    from playwright.async_api import TimeoutError as PlaywrightTimeout

    # Some tenants (e.g. Lockheed Martin) show a one-time welcome modal on
    # first load that intercepts pointer events and blocks the tab click.
    try:
        await page.click(".modalClose", timeout=2_000)
    except PlaywrightTimeout:
        pass
    try:
        await page.click("button:has-text('Job Description')", timeout=3_000)
        await page.wait_for_function(
            "document.querySelector('#job-description-container')?.textContent?.trim()?.length > 0",
            timeout=8_000,
        )
    except PlaywrightTimeout:
        pass


async def _fetch_html(url: str) -> str:
    nebius_html = await _fetch_nebius_greenhouse_html(url)
    if nebius_html is not None:
        return nebius_html
    coreweave_html = await _fetch_coreweave_greenhouse_html(url)
    if coreweave_html is not None:
        return coreweave_html
    sentinelone_html = await _fetch_sentinelone_greenhouse_html(url)
    if sentinelone_html is not None:
        return sentinelone_html

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
            icims_html = await _wait_for_icims_and_extract(page, hostname)
            if icims_html is not None:
                return icims_html
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
            await _click_eightfold_description_tab(page, hostname)
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
                posted_at=parsed.get("posted_at"),
            )
            return await ingest_listing(session, payload)
    finally:
        await engine.dispose()


async def _run(url: str, dry_run: bool) -> dict:  # type: ignore[type-arg]
    url = _normalize_ashby_embed_url(url)
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
