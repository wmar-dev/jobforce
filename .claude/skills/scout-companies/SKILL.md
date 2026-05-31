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
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/jobs?limit=1
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
get = lambda k: prefs.get(k, []) if isinstance(prefs, dict) else getattr(prefs, k, [])
out = {
  'companies': [{'name': c.name, 'domain': c.domain, 'careers_url': c.careers_url} for c in cfg.search.target_companies],
  'target_roles': get('target_roles'),
  'target_locations': get('target_locations'),
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
- Filter the `companies` list to entries whose `name` matches the argument (case-insensitive)
- If no match found, stop and print:
  ```
  ❌ Company not found in config.yaml: "<argument>"
  ```

## Step 3: Look up company IDs and existing careers_url from the DB

Run:
```bash
curl -s http://localhost:8000/api/companies
```

Parse the JSON array. For each company in the filtered config list, find the matching DB record by name (case-insensitive). Note the `id` and `careers_url` for each.

## Step 4: For each company, discover and crawl the careers page

For each company, work through the following sub-steps:

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

Count all skipped entries in the off-target total. Only pass URLs that pass both filters to step 4f.

> **Note**: anchor text on most ATS platforms (Greenhouse, Lever, Workday, Ashby) is the verbatim job title. If a page uses generic link labels like "View role" or "Apply", the anchor text will not match and the URL will be skipped — in that case, disable pre-filtering for that company and fall back to fetching all URLs. If location is not visible in the snapshot near the link, skip the location check for that entry and fetch it anyway.

### 4e: Write back the discovered careers_url (only if auto-discovered in 4b)

If the careers URL was auto-discovered via probing (not from DB or config), persist it via:
```bash
curl -s -X PATCH http://localhost:8000/api/companies/<id> \
  -H "Content-Type: application/json" \
  -d '{"careers_url": "<discovered_url>"}'
```

### 4f: Ingest each pre-filtered job listing URL

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
| Named company not found | Fail with message |
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

## Notes

- Backend must be running: `make dev`
- Playwright and Chromium must be installed: `cd backend && uv run playwright install chromium`
- The `careers_url` is written back to the DB after first auto-discovery — subsequent runs skip probing
- This skill uses Playwright MCP for browser interaction; no Python browser code
- Job extraction uses Claude's judgment — page layouts vary across ATS platforms
