---
name: scout-companies
description: Crawl target companies' careers pages using Playwright MCP, extract job listing URLs, and ingest them into Jobforce. Reads target_companies from config.yaml, discovers careers pages, and hands each job URL to the scout_fetch pipeline. Use to bulk-import jobs from company career sites.
argument-hint: "[company_name]"
user-invocable: true
---
# Scout Companies

Bulk-crawl careers pages for all target companies in `config.yaml` and ingest discovered job listings.

## Usage

```
/scout-companies [company_name]
```

- **No argument**: crawl all companies in `config.yaml` `search.target_companies`
- **With argument**: crawl only the named company (case-insensitive match on `name` field)

## Step 1: Validate backend is reachable

Run:
```bash
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/jobs?limit=1"
```

If the response is not `200`, stop immediately and print:
```
❌ Backend not reachable at http://localhost:8000. Start it with: make dev
```

## Step 2: Load target companies and user preferences from config

Run:
```bash
cd backend && uv run python -c "
import json
from jobforce.config import load_config
cfg = load_config()
prefs = cfg.user.preferences if cfg.user and cfg.user.preferences else {}
get_pref = lambda k: prefs.get(k, []) if isinstance(prefs, dict) else getattr(prefs, k, [])
search = cfg.search
get_search = lambda k: getattr(search, k, None) or []
out = {
  'companies': [{'name': c.name, 'domain': c.domain, 'careers_url': c.careers_url} for c in search.target_companies],
  'target_roles': get_pref('target_roles'),
  'target_locations': get_search('target_locations'),
}
print(json.dumps(out))
"
```

Parse the JSON object. Store `companies`, `target_roles`, and `target_locations` lists for use in filtering later.

If `companies` is empty, stop and print:
```
❌ No target_companies found in config.yaml. Add companies under search.target_companies.
```

If `target_roles` is empty, print a warning and proceed without title filtering:
```
⚠ No target_roles set in config.yaml — all job titles will be ingested.
```

If `target_locations` is empty, print a warning and proceed without location filtering:
```
⚠ No target_locations set in config.yaml — all locations will be ingested.
```

**If an argument was provided** (e.g. `/scout-companies "Acme Corp"`):
- If the argument looks like a URL (starts with `http://` or `https://`):
  - Treat it as a `careers_url` for an unknown company
  - Infer `name` from the URL (e.g. `anthropic` from `jobs.ashbyhq.com/anthropic` → `Anthropic`; use the path segment or hostname)
  - Infer `domain` as the base domain of the URL (e.g. `anthropic.com`) — if it's an ATS-hosted URL (ashbyhq.com, greenhouse.io, lever.co, etc.) leave `domain` blank
  - Set `careers_url` to the provided URL
  - Proceed to Step 2b to check if this company is already in config before adding
- Else: filter the `companies` list to entries whose `name` matches the argument (case-insensitive)
  - If no match found, proceed to Step 2b to add it

## Step 2b: Add new company to config.yaml if not already present

If the argument-provided company (by name or URL) was **not found** in the existing `companies` list:

1. Confirm the inferred `name`, `domain`, and `careers_url` with a one-line print:
   ```
   ➕ New company: <name> | domain: <domain> | careers_url: <careers_url>
   ```

2. Append the new entry to `config.yaml` under `search.target_companies`. Read the current config.yaml, find the `target_companies:` block, and append at the end in the same YAML format used by existing entries:
   ```yaml
       - name: "<name>"
         domain: "<domain>"
         careers_url: "<careers_url>"
   ```

3. Add the new company to the in-memory `companies` list so the current run processes it.

4. If the argument was a name with no URL (not a URL argument), set `careers_url` to `""` and `domain` to `""` — the skill will probe common paths in step 4b.

## Step 3: Look up company IDs and existing careers_url from the DB

Run:
```bash
curl -s http://localhost:8000/api/companies
```

Parse the JSON array. For each company in the filtered config list, find the matching DB record by name (case-insensitive). Note the `id` and `careers_url` for each.

## Step 4: For each company, discover and crawl the careers page

For each company, work through the following sub-steps:

### 4-HN: Hacker News thread detection (check first, before all other 4x steps)

**If the company's `careers_url` contains `news.ycombinator.com`**, treat it as an HN "Who's Hiring" thread — do NOT use Playwright or the normal careers-page flow:

1. Run the `hn_thread` CLI to extract all top-level comment URLs:
   ```bash
   cd backend && uv run python -m jobforce.cli.hn_thread "<careers_url>"
   ```
   Parse the JSON array printed to stdout. If the array is empty or the command fails (non-zero exit), report:
   ```
   🏢 <name> (<careers_url>) — hn_thread failed or returned 0 comments
   ```
   and skip to the next company.

2. Print:
   ```
   🏢 <name> (HN thread) — found <N> comments
   ```

3. For each comment URL in the array, run scout_fetch and ingest it exactly as step 4g does for normal job URLs (re-use the same logic: run scout_fetch, parse JSON, apply title/location filters, POST to `/api/ingest`, track 201/409/error).

4. Skip steps 4a through 4h entirely for this company — jump straight to the per-company summary in Step 5.

---

### 4a: Determine the careers URL to use

- If the DB record has a non-empty `careers_url` → use it directly (skip probing)
- Else if the config entry has a non-empty `careers_url` → use it directly (skip probing)
- Else if the company has a non-empty `domain` → proceed to 4b (probe common paths)
- Else → skip company and report: `⚠ <name> — skipped: no domain or careers_url`

### 4b: Probe common careers page paths (only if no careers_url set)

Try navigating (via Playwright MCP `browser_navigate`) to each of these URLs in order, stopping at the first that loads successfully and contains job-listing-like links:
1. `https://<domain>/careers`
2. `https://<domain>/jobs`
3. `https://<domain>/openings`
4. `https://<domain>/join-us`

A page "loads successfully" if Playwright does not throw an error and the snapshot contains anchor tags with hrefs that look like individual job postings (path segments like `/jobs/`, `/roles/`, `/positions/`, `/opening/`, numeric IDs, or job-title-like slugs).

If none of the four paths succeeds, skip and report:
```
🏢 <name> — careers page not found
  ⚠ Skipped: /careers, /jobs, /openings, /join-us all failed
```

### 4c: Navigate to the careers page with Playwright MCP

Use `browser_navigate` to load the careers URL determined in 4a or 4b. Take a snapshot with `browser_snapshot`.

If the page appears login-gated (redirects to a login form, shows sign-in wall), skip and report:
```
🏢 <name> — requires login
  ⚠ Skipped: careers page requires authentication
```

### 4d: Extract individual job listing URLs and pre-filter by anchor text

From the Playwright snapshot, extract `(anchor_text, href)` pairs where the href looks like an individual job posting link. Criteria for the href:
- Contains path segments like `/jobs/`, `/roles/`, `/positions/`, `/opening/`, `/job/`, `/careers/`
- Contains a numeric ID or a job-title-like slug (words separated by hyphens)
- **Exclude** navigation links, filter links, category pages, "apply" links that just open forms, mailto/tel links, and external social media links

Deduplicate by href. If the list is empty, report:
```
🏢 <name> (<careers_url>) — no job listings found
```

**Pre-filter by anchor text and location** (skip title check if `target_roles` is empty; skip location check if `target_locations` is empty):

For each `(anchor_text, location_text, href)` tuple (where `location_text` is any visible location label near the link):

1. **Title check**: if `target_roles` is non-empty and the anchor text does not plausibly match any target role, skip immediately:
   ```
     ⏭ skipped (off-target title): <anchor_text> — <url>
   ```

2. **Location check**: if `target_locations` is non-empty and the location text does not contain any entry from `target_locations` (case-insensitive substring match, also treat "Remote" as matching), skip immediately:
   ```
     ⏭ skipped (off-target location): <anchor_text> @ <location_text> — <url>
   ```

Count all skipped entries in the off-target total. Only pass URLs that pass both filters to step 4g.

> **Note**: anchor text on most ATS platforms (Greenhouse, Lever, Workday, Ashby) is the verbatim job title. If a page uses generic link labels like "View role" or "Apply", the anchor text will not match and the URL will be skipped — in that case, disable pre-filtering for that company and fall back to fetching all URLs. If location is not visible in the snapshot near the link, skip the location check for that entry and fetch it anyway.

### 4e: Write back the discovered careers_url (only if auto-discovered in 4b)

If the careers URL was auto-discovered via probing (not from DB or config), persist it via:
```bash
curl -s -X PATCH http://localhost:8000/api/companies/<id> \
  -H "Content-Type: application/json" \
  -d '{"careers_url": "<discovered_url>"}'
```

### 4f: Parse-sanity check on the first URL before batch

Before ingesting the full list, do a dry-run parse on the first URL to confirm the adapter works:

```bash
cd backend && uv run python -m jobforce.cli.scout_fetch --dry-run --url "<first_url>"
```

Inspect the JSON output:
- If `title` is empty or null → stop this company and report:
  ```
  🏢 <name> — parse check failed: title not extracted from <first_url>
    ⚠ Skipped batch. Fix the site adapter in backend/jobforce/services/parse.py before re-running.
  ```
- If `location` is null and `target_locations` is non-empty → warn but continue (location check will fall back to per-URL skipping):
  ```
    ⚠ location not extracted — location filtering will be skipped for this site
  ```
- If the command fails or returns non-JSON → stop this company and report:
  ```
  🏢 <name> — parse check failed: scout_fetch error on <first_url>
    ⚠ Skipped batch.
  ```

If the parse check passes, proceed to ingest the full list (including the first URL).

### 4g: Ingest each pre-filtered job listing URL

For each URL that passed the anchor-text filter in 4d:

1. Run scout_fetch:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --url "<url>"
   ```

2. If scout_fetch fails or returns non-JSON output, log: `  ❌ fetch failed: <url>` and continue.

3. Parse the JSON output. **Confirm title and location relevance**:
   - Re-apply the title check against the extracted `title`. If it no longer matches, log and skip:
     ```
       ⏭ skipped (off-target title): <title> — <url>
     ```
   - If `target_locations` is non-empty, check the extracted `location` against `target_locations`. If it doesn't match, log and skip:
     ```
       ⏭ skipped (off-target location): <title> @ <location> — <url>
     ```
   Count skipped-off-target separately from duplicates.

4. Build the ingest payload for matching titles (exclude `compensation`):
   ```json
   {
     "source_url": "...",
     "html": "",
     "title": "...",
     "company_name": "...",
     "location": "...",
     "role_type": "...",
     "description": "..."
   }
   ```

5. POST to ingest:
   ```bash
   curl -s -X POST http://localhost:8000/api/ingest \
     -H "Content-Type: application/json" \
     -d '<payload>'
   ```

6. Track the result:
   - **201**: count as ingested
   - **409**: count as duplicate (skip)
   - Other: log as error and continue

### 4h: Verify location parsed correctly

After ingesting a batch of jobs for a company, spot-check that `location` is non-null on the ingested records:

```bash
curl -s "http://localhost:8000/api/jobs?limit=50" | python3 -c "
import json,sys
d=json.load(sys.stdin)
bad=[j for j in d['items'] if j.get('company',{}).get('name','')=='<company_name>' and not j.get('location')]
print(f'{len(bad)} jobs missing location')
for j in bad[:5]: print(f'  id={j[\"id\"]} {j[\"title\"]}')
"
```

If any jobs are missing location, the site adapter's location selector is broken (e.g. ATS updated its CSS classes). Fix it before continuing:

1. **Inspect the live page** — fetch one failing URL with scout_fetch and check what came back:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --url "<failing_url>" 2>/dev/null
   ```
   If `location` is null, the adapter selector needs updating.

2. **Capture a fixture** — save a minimal but representative HTML snippet from the broken page as a new fixture file in `backend/tests/fixtures/`. Name it `<ats>_<company>_job.html` (e.g. `ashby_decagon_job.html`). Include enough markup to exercise the location selector: the `<h1>` title element, the location container, and the description container. Strip unrelated boilerplate.

3. **Add failing tests first** — in `backend/tests/unit/test_parse_service.py`, add tests using the new fixture that assert the correct `location` value. Run them to confirm they fail:
   ```bash
   cd backend && uv run pytest tests/unit/test_parse_service.py -q -k "new_fixture_name"
   ```

4. **Fix the adapter** — update the relevant `_<ats>_location()` function in `backend/jobforce/services/parse.py`. Keep the old selector as a fallback so existing fixtures continue to pass. Add a comment explaining what changed and why.

5. **Run all parse tests** — confirm all fixtures pass (new and old):
   ```bash
   cd backend && uv run pytest tests/unit/test_parse_service.py -q
   ```

6. **Backfill locations** — update the already-ingested jobs missing location via PATCH:
   ```bash
   curl -s -X PATCH "http://localhost:8000/api/jobs/<id>" \
     -H "Content-Type: application/json" \
     -d '{"location": "<location>"}'
   ```

7. **Commit** — include the fixture, the tests, and the parse fix in one commit.

## Step 5: Print per-company summary and final totals

For each company processed, print:
```
🏢 <name> (<careers_url_used>)
  ✅ <n> ingested  ⏭ <n> duplicate  ⏭ <n> off-target
```

Or for failures:
```
🏢 <name> — careers page not found
  ⚠ Skipped: no careers_url and /careers, /jobs, /openings, /join-us all failed
```

After all companies:
```
─────────────────────────────
Total: <n> ingested, <n> duplicate, <n> off-target, <n> company/companies failed
```

## Error handling reference

| Condition | Behaviour |
| --------- | --------- |
| Backend not reachable | Fail immediately with instructions |
| No companies in config | Fail with message |
| Named company not found in config | Add to config.yaml and proceed |
| URL argument provided | Infer company name/domain, add to config.yaml if new, proceed |
| No domain or careers_url | Skip company, report |
| Careers page not found after probing | Skip company, report |
| Login-gated page | Skip company, report "requires login" |
| No job links found on page | Report, continue to next company |
| scout_fetch fails for a URL | Log error for that URL, continue |
| Anchor text doesn't match target_roles | Log as off-target (title), skip scout_fetch entirely, continue |
| Location text doesn't match target_locations | Log as off-target (location), skip scout_fetch entirely, continue |
| Fetched title doesn't match target_roles | Log as off-target (title), skip ingest, continue |
| Fetched location doesn't match target_locations | Log as off-target (location), skip ingest, continue |
| All anchor texts are generic (e.g. "View role") | Disable title pre-filtering, fall back to fetching all URLs |
| Location not visible near link in snapshot | Skip location pre-filter for that entry, fetch it anyway |
| No target_roles in config | Warn once, skip title filtering, ingest all titles |
| No target_locations in config | Warn once, skip location filtering, ingest all locations |

## Step 6: Run oracle-rank on newly ingested jobs

After printing the final totals, invoke the oracle-rank skill to score the new listings:

```
/oracle-rank
```

This scores only unscored jobs, so it will pick up exactly what was just ingested without re-scoring existing records.

## Notes

- Backend must be running: `make dev`
- Playwright and Chromium must be installed: `cd backend && uv run playwright install chromium`
- The `careers_url` is written back to the DB after first auto-discovery — subsequent runs skip probing
- New companies (from a URL or unknown name argument) are appended to `config.yaml` automatically so they persist for future runs
- This skill uses Playwright MCP for browser interaction; no Python browser code
- Job extraction uses Claude's judgment — page layouts vary across ATS platforms
