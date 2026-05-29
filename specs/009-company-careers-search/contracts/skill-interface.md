# Skill Interface Contract: scout-companies

## Invocation

```text
/scout-companies [company_name]
```

- **No argument**: crawl all companies in `config.yaml` `search.target_companies`
- **With argument**: crawl only the named company (case-insensitive match on `name` field)

## Prerequisites

- Backend running at `http://localhost:8000` (checked before crawling)
- `playwright` + Chromium installed: `cd backend && uv run playwright install chromium`
- At least one entry in `config.yaml` `search.target_companies`

## Steps

1. **Validate backend** — `GET http://localhost:8000/api/jobs?limit=1`; fail fast if unreachable
2. **Load companies** — read `config.yaml` `search.target_companies`; filter by argument if provided
3. **For each company**:
   a. If `careers_url` set → use it directly
   b. If `domain` set → probe `/careers`, `/jobs`, `/openings`, `/join-us` in order; use first that responds
   c. If neither → skip with warning
   d. Navigate to careers URL via Playwright MCP
   e. Extract individual job listing URLs from the page
   f. If URL was auto-discovered: write back via `PATCH /api/companies/{id}` with `careers_url`
   g. For each URL: run `scout_fetch` CLI → POST to `/api/ingest`
4. **Report** per-company summary and totals

## Output Format

```text
🏢 Acme Corp (acme.com/careers)
  ✅ 3 ingested  ⏭ 1 skipped (duplicate)

🏢 Example Inc — careers page not found
  ⚠ Skipped: no careers_url and /careers, /jobs, /openings, /join-us all failed

─────────────────────────────
Total: 3 ingested, 1 duplicate, 1 company failed
```

## Error Handling

| Condition | Behaviour |
| --------- | --------- |
| Backend not reachable | Fail immediately, print instructions |
| No companies in config | Fail with "No target_companies in config.yaml" |
| Named company not found | Fail with "Company not found in config.yaml" |
| Careers page not found | Skip company, report, continue |
| Login-gated careers page | Skip company, report "requires login", continue |
| `scout_fetch` fails for a URL | Log error for that URL, continue with remaining |
