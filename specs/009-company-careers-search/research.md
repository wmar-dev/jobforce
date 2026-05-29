# Research: Company Careers Search Skill

## Findings

### 1. Existing ingest pipeline is fully reusable

`scout_fetch` CLI takes `--url`, fetches headlessly via Playwright, runs `parse_html()`, and prints JSON. `/scout-crawl` skill then POSTs to `POST /api/ingest`. The new skill does the same — the only new step is discovering the list of job URLs from a careers page before iterating.

### 2. `CompanyConfig` change is a one-line addition

`config.py` `CompanyConfig` already has `name: str` and `domain: str = ""`. Adding `careers_url: str = ""` follows the same pattern. No DB migration, no seed changes, no other files affected.

### 3. Career page discovery is judgment-based — skill is the right tool

ATS platforms (Greenhouse, Lever, Workday, Ashby) each render job listings differently. A fixed-path probe (`/careers`, `/jobs`) combined with Claude's link extraction judgment covers the common cases. `careers_url` handles everything else.

### 4. No new backend endpoint needed

The skill calls `scout_fetch` CLI per-URL (same as `/scout-crawl`), then POSTs to the existing `/api/ingest`. The backend is unchanged except for the config model.

### 5. Concurrency: sequential per-company, parallel URLs optional but deferred

For simplicity, process companies sequentially. Job URL ingestion per company can be sequential too — the bottleneck is Playwright page loads, not CPU. Parallelism is a future optimization if needed.
