---
name: parse-adapter-update
description: Inspect a job posting URL, capture an HTML fixture, write failing tests, and add or update the backend's site-specific parser adapter in backend/jobforce/services/parse.py — the parser used by scout_fetch and /scout-companies for automated crawling. Use when scout_fetch fails to extract title/company_name/location/description for a site, or when /scout-companies reports a parse check failure (step 4f/4h).
argument-hint: "<url> [job_id]"
user-invocable: true
---

# Parse Adapter Update

Inspect a job posting URL, capture a minimal HTML fixture, write test-first
assertions, then add or update the site-specific adapter in
`backend/jobforce/services/parse.py`. This is the **backend** parser used by
`scout_fetch` / `/scout-companies` for automated crawling — a separate
registry from the Chrome extension's `content.js` (see `/site-adapter-update`
for that one).

## Usage

```
/parse-adapter-update <url> [job_id]
```

- `<url>`: a direct job listing URL (not a careers index/homepage)
- optional `job_id`: an already-ingested job's DB id — if its `location`/
  `description`/etc. are null because of this same parse bug, it gets
  backfilled once the adapter is fixed

## Step 1: Validate Input

If no URL argument was provided, print:

```
❌ Usage: /parse-adapter-update <url> [job_id]
```

Then stop.

## Step 2: Check Current Parse Output

Run:

```bash
cd backend && uv run python -m jobforce.cli.scout_fetch --dry-run --url "<url>"
```

- **Command fails** (`page does not look like a job listing`, `company_name=None`
  and/or `title=None`): proceed — this is the primary case.
- **Command succeeds**: inspect the JSON. If `title`, `company_name`,
  `location`, and `description` are all non-null and look correct, print the
  JSON and:
  ```
  ✅ <hostname> already parses correctly — title, company_name, location, and
     description all extracted. Nothing to fix.
  ```
  Stop, unless the user explicitly asked for an additional field (e.g.
  `compensation`) — in that case proceed with just that field in scope.
- If some fields are populated and others are null, note which are missing —
  this scopes the adapter functions you'll need to write in Step 7.

## Step 3: Capture an HTML Fixture via Playwright MCP

Navigate to `<url>` with `mcp__playwright__browser_navigate` (skip if the
browser is already on this exact page from a prior step in this session).

If navigation fails or the page errors, print:

```
❌ Could not load <url>: <reason>
```

Then stop — do not modify any files.

Retrieve the fully-rendered HTML with `mcp__playwright__browser_evaluate`:

```js
() => document.documentElement.outerHTML
```

(Use this rather than a plain `curl`/`fetch` — many of these sites are
client-rendered SPAs, and `parse_html` must work against the same DOM
`scout_fetch`'s headless browser produces.)

## Step 4: Determine Hostname, Adapter Status, and Naming

Compute `hostname = urlparse(url).hostname`, stripping a leading `www.` —
this must match `parse.py`'s own normalization (`parse_html`).

Check `backend/jobforce/services/parse.py`'s `SITE_ADAPTERS` dict:

- **Hostname not present** (and no suffix match via `_match_adapter`'s
  subdomain logic, e.g. `*.myworkdayjobs.com`): this is a **new adapter**.
  Infer the canonical company name from the page (logo `alt` text, footer
  copyright, `<title>`, or `og:site_name`) — cross-check against
  `config.yaml`'s `search.target_companies` for this domain if an entry
  exists, for correct casing.
  - Fixture name: `<company_slug>_job.html` (lowercase, underscores —
    e.g. `larridin_job.html`)
  - Test section name: `<company_slug>` (e.g. `larridin`)

- **Hostname already present**: this is an **existing shared-ATS adapter**
  (Ashby, Greenhouse, Workday, Lever, Workable, Notion, etc.) that doesn't
  handle this particular company's page layout correctly. Use the
  `<ats>_<company>_job.html` naming convention already established for this
  case (e.g. `ashby_decagon_job.html`):

  | `SITE_ADAPTERS` key | prefix |
  | --- | --- |
  | `jobs.ashbyhq.com` | `ashby` |
  | `job-boards.greenhouse.io` / `boards.greenhouse.io` | `greenhouse` |
  | `myworkdayjobs.com` | `workday` |
  | `jobs.lever.co` | `lever` |
  | `jobs.workable.com` | `workable` |
  | `notion.site` | `notion` |
  | anything else | derive from the existing adapter's hostname |

## Step 5: Trim and Write the Fixture

Existing fixtures in `backend/tests/fixtures/` are minimal — typically
under 2KB, hand-trimmed to just the markup needed to exercise selectors
(title heading, location element/paragraph, description container, and
their immediate structural context). Trim the captured HTML the same way:

- Keep: the title heading, the elements/containers holding location,
  description, compensation, and role-type signals, and enough surrounding
  structure (parent classes/ids) for your selectors to anchor on.
- Strip: `<script>`, `<style>`, nav/header/footer chrome, unrelated widgets,
  tracking iframes, SVG icon bodies.
- Preserve real class names, ids, and tag structure exactly as rendered —
  selectors must match this fixture AND the live page.

Write the trimmed HTML to `backend/tests/fixtures/<name>.html`.

## Step 6: Git Guard

Run:

```bash
git diff --name-only backend/jobforce/services/parse.py backend/tests/unit/test_parse_service.py
```

If this produces any output, print:

```
⚠️ parse.py or test_parse_service.py has uncommitted changes.
   Commit or stash them before running this skill.
```

Then stop — do not modify any files. (The new fixture file itself is
untracked and fine.)

## Step 7: Write Failing Tests (Test-First)

`test_parse_service.py` is written test-first — new adapter coverage follows
the same pattern as the existing `# AdaL (adalagent.ai)` section near the end
of the file.

**New adapter**: append a new section:

```python
# ---------------------------------------------------------------------------
# <Company> (<hostname>) — <one-line note on page structure / quirks>
# ---------------------------------------------------------------------------

_<COMPANY>_URL = "<url>"


def test_parse_html_<company>_title() -> None:
    from jobforce.services.parse import parse_html

    html = _read("<fixture>.html")
    result = parse_html(html, _<COMPANY>_URL)
    assert result["title"] == "<expected title>"


def test_parse_html_<company>_company() -> None:
    ...
    assert result["company_name"] == "<Company>"


def test_parse_html_<company>_location() -> None:
    ...
    assert result["location"] == "<expected location>"


def test_parse_html_<company>_description_non_null() -> None:
    ...
    assert result["description"] is not None
    assert "<distinctive phrase from the description>" in result["description"]
```

Only write tests for fields noted as missing in Step 2 — if `title` already
extracts correctly via the generic adapter, don't add a redundant test/override
for it.

**Existing-ATS adapter with a layout bug**: add tests to that adapter's
existing test section (don't create a new section), parameterized on the new
fixture — mirror how `ashby_decagon_job.html` tests sit alongside the base
`ashby_job.html` tests.

Run the new tests and confirm they **fail**:

```bash
cd backend && uv run pytest tests/unit/test_parse_service.py -q -k "<company>"
```

If a test unexpectedly passes already, the generic adapter handles that
field — delete that test rather than writing a needless override.

## Step 8: Implement the Adapter, Then Verify

Add/update functions in `parse.py` near the relevant section (or a new
section, following the existing `# --- Company (hostname) ---` comment-block
style):

- Prefer `doc.select_one(...)` with real classes/ids from the fixture, or
  structural relationships (`find_next_sibling`, heading + next element)
  over brittle nth-child paths.
- Use `_text()` for plain-text fields, `_to_markdown()` for `description`.
- A field with a fixed value (the adapter only ever serves one company) is a
  one-line lambda: `"company_name": lambda doc, url: "<Company>"`.
- **Existing-ATS adapter**: keep the old selector working as a fallback
  (try the new selector first, fall back to the old) so existing fixtures for
  other companies on that ATS continue to pass.
- Register/update the entry in `SITE_ADAPTERS`, including only the fields
  this adapter overrides — everything else falls through to
  `GENERIC_ADAPTER`.

Iterate until green, then check for regressions and quality gates:

```bash
cd backend && uv run pytest tests/unit/test_parse_service.py -q
cd backend && uv run ruff check jobforce/services/parse.py tests/unit/test_parse_service.py
cd backend && uv run ruff format --check jobforce/services/parse.py tests/unit/test_parse_service.py
cd backend && uv run mypy jobforce/services/parse.py
```

Fix anything that doesn't pass before continuing.

## Step 9: End-to-End Check, Optional Backfill, Completion Report

Re-run the dry-run fetch to confirm the live page now parses correctly:

```bash
cd backend && uv run python -m jobforce.cli.scout_fetch --dry-run --url "<url>"
```

**If `job_id` was provided**: fetch the current record, compare against the
newly-parsed values, and PATCH any field that was previously null/wrong:

```bash
curl -s http://localhost:8000/api/jobs/<job_id> | python3 -m json.tool
curl -s -X PATCH "http://localhost:8000/api/jobs/<job_id>" \
  -H "Content-Type: application/json" \
  -d '{"location": "...", "description": "..."}'
```

**If no `job_id` and the job isn't ingested yet**, offer to ingest it now
(drop `--dry-run`):

```bash
cd backend && uv run python -m jobforce.cli.scout_fetch --url "<url>"
```

Print a completion report:

```
✅ Adapter <added|updated> for <hostname>
   Fixture: backend/tests/fixtures/<name>.html
   New tests: <comma-separated test names>
   Adapter fields: <comma-separated fields with site-specific extractors>
   Fragile selectors (if any): <list or "none">
   pytest / ruff / mypy: all passing
   <backfill / ingest result, if applicable>
```

## Notes

- The Playwright MCP server must be running: `claude mcp list` should show
  `playwright`. If missing:
  `claude mcp add --transport stdio playwright -- npx -y @playwright/mcp@latest`
- This skill is the codified version of `/scout-companies` step 4h
  ("Verify location parsed correctly" → fix adapter) — run it directly when
  you already have a failing URL, or when `/scout-companies` flags a parse
  check failure (step 4f).
- This skill only touches `backend/jobforce/services/parse.py`,
  `backend/tests/unit/test_parse_service.py`, and
  `backend/tests/fixtures/`. For the Chrome extension's capture-on-click
  adapter (`chrome-extension/content.js`), use `/site-adapter-update`.
- Run the skill twice on the same URL to verify idempotency — the second run
  should report "already parses correctly" in Step 2.
