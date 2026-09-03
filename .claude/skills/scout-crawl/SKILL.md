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

5. Report result:
   - **`duplicate: false`**: "✅ Captured: [title] at [company] — Job #[id]"
   - **`duplicate: true`**: "Already saved — this listing is in your board (Job #[id])"
   - **Command error / non-zero exit**: "❌ Ingest failed: [stderr detail]"

## Notes

- The backend does not need to be running — `scout_fetch` writes directly to the SQLite database.
- `playwright` and Chromium must be installed: `cd backend && uv sync && uv run playwright install chromium`
- The parser uses site-specific adapters. For unsupported sites the generic adapter runs.
- Login-gated pages are not supported; the tool will time out or return incomplete data.
- To add a new site adapter, add a module to `backend/jobforce/services/parse/sites/` (see `/parse-adapter-update`).
- Use `--dry-run` to parse without writing to the database.
