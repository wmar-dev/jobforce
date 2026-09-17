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

Use the `config_lookup` CLI:

**No argument — all companies:**
```bash
cd backend && uv run python -m jobforce.cli.config_lookup
```

**Argument provided — single company lookup (infer the name first, then pass it):**
```bash
cd backend && uv run python -m jobforce.cli.config_lookup "<inferred_name>"
```

Replace `<inferred_name>` with the company name inferred from the argument (see rules below). The output includes `total_companies` when a name filter is used — a non-zero value confirms the config was read even when `companies` is empty (i.e. a genuinely new company, not a broken config).

Parse the JSON object. Store `companies`, `target_roles`, and `target_locations` lists for use in filtering later.

If **no argument** and `companies` is empty, stop and print:
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

Also read `config/scouting-notes.md` from disk if it exists. This file may
contain `## Avoid` and `## Prefer` sections with freeform guidance on
companies, industries, or role patterns — use it as an additional judgment
signal in the title checks in 4d and 4g (alongside, not instead of,
`target_roles`). If the file is absent, proceed without it.

**If an argument was provided** (e.g. `/scout-companies "Acme Corp"`):
- If the argument looks like a URL (starts with `http://` or `https://`):
  - Treat it as a `careers_url` for an unknown company
  - Infer `name` from the URL (e.g. `widgetco` from `jobs.ashbyhq.com/widgetco` → `Widgetco`; use the path segment or hostname)
  - Infer `domain` as the base domain of the URL (e.g. `widgetco.com`) — if it's an ATS-hosted URL (ashbyhq.com, greenhouse.io, lever.co, etc.) leave `domain` blank
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

Use `browser_navigate` to load the careers URL determined in 4a or 4b. Take a snapshot with `browser_snapshot` using `depth: 3` — job titles and hrefs are in the top few layers of the accessibility tree, and a shallow snapshot cuts token cost by ~70% on large listing pages.

If the page appears login-gated (redirects to a login form, shows sign-in wall), skip and report:
```
🏢 <name> — requires login
  ⚠ Skipped: careers page requires authentication
```

### 4c2: Try filtering by location and team via the page's own search controls (optional)

Large careers pages (100+ listings across many pages) often expose their own filter UI — a **Location** combobox/listbox, a **Team**/**Department**/**Category**/**Function** combobox/listbox, sometimes a Keywords box, and a Search/Apply/Filter button. Using these first can shrink a multi-page crawl down to a handful of relevant listings.

In the snapshot from 4c, look for such controls. If none are found, or `target_roles`/`target_locations` are both empty, skip this step entirely and proceed to 4d with the unfiltered snapshot — log:
```
🔎 <name> — no usable filter controls found, crawling unfiltered
```

If controls are found:

1. **Location filter** (skip if `target_locations` is empty): find option(s) whose text matches a `target_locations` entry (case-insensitive substring; "Remote" matches "Remote"). There may be more than one match (e.g. both "San Francisco" and "Remote" are offered).
   - **Multi-select** (checkboxes or a multi-select listbox): select all matching options in a single pass.
   - **Single-select** (`combobox`/`<select>`): plan one pass per matching option (see step 4 below).
   - No matches → leave the location filter unset.

2. **Team/department filter** (skip if `target_roles` is empty): find an option whose text suggests it covers `target_roles` — keywords like "Engineering", "Software", "Technology", "R&D", "Research", "Product & Engineering". Most engineering-flavored `target_roles` (e.g. "Software Engineer", "ML Engineer", "Staff Software Engineer") fall under an "Engineering"-style category.
   - Exactly one option clearly covers all (or nearly all) `target_roles` → select it.
   - Ambiguous (no clear match, or `target_roles` span categories like both "Engineering" and "Research") → leave unset rather than risk excluding valid jobs.

3. If neither a location nor a team filter could be mapped to an available option, treat this the same as "no usable filter controls found" (log and fall back to 4d unfiltered).

4. Apply the filter(s) with `browser_select_option` (or by clicking checkboxes), then click the Search/Filter/Apply button with `browser_click`, then take a new snapshot with `browser_snapshot` using `depth: 3`.
   - Single-select location with N matching options → repeat this for each option (N passes total), each time re-applying the team filter (if any) alongside that pass's location.

5. For each filtered snapshot, run the link-extraction + pre-filter logic from 4d against it (instead of the unfiltered 4c snapshot), producing a list of `(anchor_text, location_text, href)` tuples. Merge tuples across passes, deduplicating by `href`.
   - If a filtered snapshot shows zero results where the unfiltered count was non-zero, the filter mapping was likely wrong for this site — discard that pass's results and fall back to the unfiltered 4c snapshot for 4d instead.

6. Log which filters were applied (one line per pass):
   ```
   🔎 <name> — filtering by Team=<team>, Location=<location>
   ```

7. Pass the merged, deduplicated tuple list to 4e onward as if it were the output of 4d. Skip the unfiltered 4d extraction in this case.

> This is a pre-filter to reduce crawl volume on large listing pages — it does not replace the anchor-text/location pre-filter in 4d (still applied per-pass in step 5), nor the post-fetch checks in 4g.

### 4d: Extract individual job listing URLs and pre-filter by anchor text

If 4c2 already produced a merged tuple list, skip this step and proceed to 4e with that list.

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
   If `target_roles` matches (or is empty) but the anchor text clearly matches an `## Avoid` entry from `config/scouting-notes.md` (e.g. the anchor text or nearby context indicates a staffing agency posting), skip it the same way:
   ```
     ⏭ skipped (scouting-notes: avoid): <anchor_text> — <url>
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
- If `title` is empty or null, or the command fails or returns non-JSON → attempt an automatic fix before giving up. Invoke the parse-adapter-update skill on this URL:
  ```
  /parse-adapter-update <first_url>
  ```
  Then re-run the dry-run parse check above.
  - If `title` now extracts correctly → log and proceed to ingest the full list:
    ```
    🔧 <name> — adapter fixed for <hostname>, proceeding with batch
    ```
  - If it still fails after the fix attempt → stop this company and report:
    ```
    🏢 <name> — parse check failed: title not extracted from <first_url> (auto-fix attempted, still failing)
      ⚠ Skipped batch. Fix the site adapter in backend/jobforce/services/parse/sites/ before re-running.
    ```
- If `location` is null and `target_locations` is non-empty → warn but continue (location check will fall back to per-URL skipping):
  ```
    ⚠ location not extracted — location filtering will be skipped for this site
  ```

If the parse check passes (on the first try or after an auto-fix), proceed to ingest the full list (including the first URL).

### 4g: Ingest each pre-filtered job listing URL

For each URL that passed the anchor-text filter in 4d:

1. **Dedup check before crawling**:
   ```bash
   curl -s "http://localhost:8000/api/jobs?source_url=<url>"
   ```
   If `total >= 1`, the job is already captured — count it as a duplicate and continue to the next URL without running scout_fetch:
   ```
     ⏭ duplicate (already captured): <url>
   ```

2. Run scout_fetch with `--dry-run` — this step is parse-only. Without `--dry-run`, scout_fetch writes the job straight to the database itself (see `_ingest` in `backend/jobforce/cli/scout_fetch.py`), which would ingest it before the title/location re-check in step 4 has a chance to reject it:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --dry-run --url "<url>"
   ```

3. If scout_fetch fails or returns non-JSON output, log: `  ❌ fetch failed: <url>` and continue.

4. Parse the JSON output. **Confirm title and location relevance**:
   - Re-apply the title check against the extracted `title`. If it no longer matches, log and skip:
     ```
       ⏭ skipped (off-target title): <title> — <url>
     ```
   - If `target_locations` is non-empty, check the extracted `location` against `target_locations`. If it doesn't match, log and skip:
     ```
       ⏭ skipped (off-target location): <title> @ <location> — <url>
     ```
   - Re-apply the `## Avoid` check from `config/scouting-notes.md` against the extracted `title` and `description` (now that the full description is available, this catches cases the anchor-text-only check in 4d couldn't). If it matches, log and skip:
     ```
       ⏭ skipped (scouting-notes: avoid): <title> — <url>
     ```
   Count skipped-off-target separately from duplicates.

5. Build the ingest payload for matching titles (exclude `compensation`):
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
   The `description` value **must** be copied verbatim from step 2's `scout_fetch` JSON output field of the same name — never hand-write it from a raw page fetch, a WebFetch summary, or an ATS JSON API response. Those sources return rich text pre-escaped for HTML embedding (literal `&lt;div&gt;`, `&quot;`, etc.); only `scout_fetch`'s own parser (which renders the real page and converts it to clean markdown) produces a value safe to store as-is. If you ever bypass `scout_fetch` for a job (e.g. hitting an ATS API directly instead of running step 2), do not paste its raw content field into `description` — it needs `html.unescape()` at minimum, ideally re-parsed to markdown, before it's usable.

6. POST to ingest:
   ```bash
   curl -s -X POST http://localhost:8000/api/ingest \
     -H "Content-Type: application/json" \
     -d '<payload>'
   ```

7. Track the result:
   - **201**: count as ingested
   - **409**: count as duplicate (rare — step 1's pre-check should normally catch these before crawling)
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

If any jobs are missing location, the site adapter's location selector is broken (e.g. ATS updated its CSS classes). Fix it before continuing, using the parse-adapter-update skill rather than redoing its fixture/test/adapter procedure inline:

1. **Fix the adapter and backfill the first bad record** — invoke parse-adapter-update on the first failing job's URL and id (found via `source_url` on that job's record, `GET /api/jobs/<id>`):
   ```
   /parse-adapter-update <first_failing_url> <first_failing_id>
   ```
   This captures a fixture, writes failing tests, fixes the adapter's location selector (keeping the old selector as a fallback), runs the full parse test suite, and backfills that one job's `location` via PATCH.

2. **Backfill any remaining bad records** — if step 6's spot-check found more than one job missing location, the adapter is now fixed but the others still have null `location` in the DB. For each remaining bad job id:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --dry-run --url "<its_url>" 2>/dev/null
   curl -s -X PATCH "http://localhost:8000/api/jobs/<id>" \
     -H "Content-Type: application/json" \
     -d '{"location": "<location from dry-run output>"}'
   ```

3. **Commit** — parse-adapter-update does not commit on your behalf; include the new fixture, the new tests, and the adapter fix in one commit.

### 4i: Detect and merge duplicate company records

`/api/ingest` derives `company_name` from the scraped page text, which can differ from this company's name in `config.yaml`/the DB (e.g. scraped "Globotech" vs the canonical "Globo Tech"). Company lookup during ingest is an exact case-insensitive match, so a near-miss creates a new duplicate `Company` row instead of reusing the canonical one.

After ingesting this company's listings, re-fetch companies:

```bash
curl -s http://localhost:8000/api/companies
```

Look for another company record whose name, normalized (lowercase, spaces/punctuation removed), equals this company's normalized name but whose `id` differs from the canonical `id` noted in Step 3 (the canonical record is the one matching the `config.yaml` name, usually with `domain`/`careers_url` set).

If a duplicate is found, merge it into the canonical record using the `merge_companies` CLI — this reassigns the duplicate's job listings and meeting notes to the canonical company, then deletes the duplicate:

```bash
cd backend && uv run python -m jobforce.cli.merge_companies <duplicate_id> <canonical_id>
```

Log:
```
🔧 <name> — merged duplicate company id=<duplicate_id> ("<dup_name>") into id=<canonical_id>
```

If no duplicate is found, skip silently.

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
| Page has Location/Team filter controls matching target_roles/target_locations | Apply filter(s), use filtered snapshot(s) for 4d, log filters applied |
| No filter controls found, or none map to target_roles/target_locations | Skip filtering, crawl unfiltered, log fallback |
| Filtered snapshot returns zero results (unfiltered had results) | Discard that pass, fall back to unfiltered snapshot |
| No job links found on page | Report, continue to next company |
| scout_fetch fails for a URL | Log error for that URL, continue |
| Anchor text doesn't match target_roles | Log as off-target (title), skip scout_fetch entirely, continue |
| Location text doesn't match target_locations | Log as off-target (location), skip scout_fetch entirely, continue |
| `GET /api/jobs?source_url=` returns `total >= 1` | Already captured — count as duplicate, skip scout_fetch entirely, continue |
| Fetched title doesn't match target_roles | Log as off-target (title), skip ingest, continue |
| Fetched location doesn't match target_locations | Log as off-target (location), skip ingest, continue |
| All anchor texts are generic (e.g. "View role") | Disable title pre-filtering, fall back to fetching all URLs |
| Location not visible near link in snapshot | Skip location pre-filter for that entry, fetch it anyway |
| No target_roles in config | Warn once, skip title filtering, ingest all titles |
| No target_locations in config | Warn once, skip location filtering, ingest all locations |
| `config/scouting-notes.md` absent | Proceed without it — no `## Avoid`/`## Prefer` judgment applied |
| Anchor text or fetched title/description matches an `## Avoid` entry in scouting-notes.md | Log as off-target (scouting-notes), skip, continue |
| Ingest creates a duplicate Company record (4i) | Merge via `merge_companies` CLI into the canonical company, log merge |

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
- On large listing pages, the page's own Location/Team filter controls are tried first (4c2) to shrink the crawl before falling back to a full unfiltered crawl
- Duplicate company records left over from past runs (or runs predating step 4i) can be cleaned up at any time with `cd backend && uv run python -m jobforce.cli.merge_companies <duplicate_id> <canonical_id>`
- `config/scouting-notes.md` (optional, copy from `config/scouting-notes.example.md`) adds freeform `## Avoid`/`## Prefer` guidance on top of the structured `target_roles`/`target_locations` filters
