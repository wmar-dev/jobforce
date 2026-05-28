---
name: scout-crawl
description: Capture a job listing from a URL using Playwright MCP and ingest it into Jobforce. Navigates to the page, handles login if needed, extracts structured job data, and posts it to the backend. Use when you want to save a job posting from the web.
argument-hint: "<URL>"
user-invocable: true
---
# Scout Crawl — Playwright MCP Skill

Capture a job listing from a URL using Playwright MCP and ingest it into Jobforce.

## Usage

```
/scout-crawl <URL>
```

## Steps

1. Navigate to the provided URL using Playwright MCP:
   ```
   mcp__playwright__navigate({ url: "<URL>" })
   ```

2. Check if login is required. If the page shows a login form or redirects to auth:
   - Print: "Please log in to [site] in the browser window, then press Enter to continue."
   - Wait for user confirmation before proceeding.

3. Extract structured job data from the page:
   ```
   mcp__playwright__get_text({ selector: "body" })
   ```
   Also capture the page HTML:
   ```
   mcp__playwright__evaluate({ expression: "document.documentElement.outerHTML" })
   ```

4. Parse the extracted text to identify:
   - `title`: Job title (typically in `<h1>`)
   - `company_name`: Employer name
   - `location`: Job location (or "Remote")
   - `role_type`: "full-time" | "part-time" | "contract" | "internship" | null
   - `description`: Full job description text

5. POST to the Jobforce ingest API:
   ```json
   POST http://localhost:8000/api/ingest
   {
     "source_url": "<URL>",
     "html": "<extracted HTML>",
     "title": "<extracted title>",
     "company_name": "<extracted company>",
     "location": "<extracted location>",
     "role_type": "<extracted role type>",
     "description": "<extracted description>"
   }
   ```

6. Report result:
   - **201**: "✅ Captured: [title] at [company] — Job #[id]"
   - **409**: "Already saved — this listing is in your board (Job #[id])"
   - **Error**: "❌ Ingest failed: [error detail]"

## Notes

- Backend must be running: `cd backend && make dev`
- Playwright MCP must be configured: `claude mcp add playwright npx @playwright/mcp@latest`
- For auth-required sites, always pause for manual login rather than attempting automated bypass
