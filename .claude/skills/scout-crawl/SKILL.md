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

1. Run the scout fetch tool:
   ```bash
   cd backend && uv run python -m jobforce.cli.scout_fetch --url "<URL>"
   ```
   This fetches the page headlessly and parses it using site-specific adapters.

2. If the command fails with a login-related error, stop and tell the user:
   "This page requires authentication. Please log in manually and re-run once the page is accessible without login."

3. Parse the JSON printed to stdout. It contains:
   - `source_url`
   - `title`
   - `company_name`
   - `location`
   - `role_type`
   - `description`
   - `compensation` (optional)

4. POST to the Jobforce ingest API:
   ```bash
   curl -s -X POST http://localhost:8000/api/ingest \
     -H "Content-Type: application/json" \
     -d '<json from step 3 minus compensation field>'
   ```
   The ingest API accepts: `source_url`, `html` (pass empty string `""`), `title`, `company_name`, `location`, `role_type`, `description`.

   Build the payload from the parsed JSON, excluding `compensation` (not in ingest schema).

5. Report result:
   - **201**: "✅ Captured: [title] at [company] — Job #[id]"
   - **409**: "Already saved — this listing is in your board (Job #[id])"
   - **Error**: "❌ Ingest failed: [error detail]"

## Notes

- Backend must be running: `make dev`
- `playwright` and Chromium must be installed: `cd backend && uv sync && uv run playwright install chromium`
- The parser uses site-specific adapters (starting with OpenAI). For unsupported sites the generic adapter runs.
- Login-gated pages are not supported; the tool will time out or return incomplete data.
- To add a new site adapter, edit `backend/jobforce/services/parse.py` — see `quickstart.md` in the feature spec.
