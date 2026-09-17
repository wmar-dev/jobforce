---
name: scout-crawl
description: Capture a job listing from a URL using Playwright MCP and ingest it into Jobforce. Navigates to the page, handles login if needed, extracts structured job data, and posts it to the backend. Use when you want to save a job posting from the web.
argument-hint: "<URL>"
user-invocable: true
---
# Scout Crawl

Capture a job listing from a URL and ingest it into Jobforce using a deterministic Python parser.

## Usage

```
/scout-crawl <URL>
```

## Steps

0. **Validate the URL** before running anything. If the URL is a company homepage or a generic careers index page (e.g. `airbyte.com/`, `airbyte.com/careers`, `jobs.ashbyhq.com/airbyte`), do NOT pass it directly to `scout_fetch`. Instead, use Playwright MCP to browse the careers page, find individual job listing URLs, and ingest each one separately.

1. Run the scout fetch tool:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --url "<URL>"
   ```
   This fetches the page headlessly, parses it using site-specific adapters, and writes directly to the database. The backend does not need to be running.

2. If the command fails with a `page does not look like a job listing` error, the URL is a homepage or index — browse it with Playwright MCP to find individual listing URLs and ingest those instead.

3. If the command fails with a login-related error, stop and tell the user:
   "This page requires authentication. Please log in manually and re-run once the page is accessible without login."

4. Parse the JSON printed to stdout. It contains:
   - `source_url`, `title`, `company_name`, `location`, `role_type`, `description`
   - `id` — the database row id of the job listing
   - `status` — pipeline status (always `"saved"` on first capture)
   - `duplicate` — `true` if this URL was already in the database

4a. **Check for a broken adapter**: if `title`, `company_name`, `location`, or `description` came back null — the job was already written to the database in step 1 with those fields missing. Attempt an automatic fix before reporting:
   ```
   /parse-adapter-update <URL> <id>
   ```
   This fixes the site adapter and (if the backend is reachable) backfills the already-ingested record via PATCH. If the backend isn't running, the adapter is still fixed for future captures, but this record's null fields will need a manual backfill once it is (re-run `/parse-adapter-update <URL> <id>` then).

   Re-run the dry-run fetch to get corrected values for the report:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --dry-run --url "<URL>"
   ```
   Use these corrected values (or the original ones, if the fix didn't fully resolve them) in step 5's report.

5. Report result:
   - **`duplicate: false`**: "✅ Captured: [title] at [company] — Job #[id]"
   - **`duplicate: true`**: "Already saved — this listing is in your board (Job #[id])"
   - **Command error / non-zero exit**: "❌ Ingest failed: [stderr detail]"
   - **Fields still null after auto-fix attempt (4a)**: append a warning: "⚠ Captured with missing fields ([list]) — adapter fix did not fully resolve; may need manual attention"

## Notes

- The backend does not need to be running — `scout_fetch` writes directly to the SQLite database.
- `playwright` and Chromium must be installed: `cd backend && uv sync && uv run playwright install chromium`
- The parser uses site-specific adapters. For unsupported sites the generic adapter runs.
- Login-gated pages are not supported; the tool will time out or return incomplete data.
- To add a new site adapter, add a module to `backend/jobforce/services/parse/sites/` (see `/parse-adapter-update`).
- Use `--dry-run` to parse without writing to the database.
