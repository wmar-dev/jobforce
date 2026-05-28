# Quickstart: Scout Crawl Deterministic Parser

## Running the parser directly

```bash
cd backend
uv run python -m jobforce.cli.parse_job \
  --url "https://openai.com/careers/some-role/" \
  --html-file /path/to/page.html
```

Output (JSON on stdout):
```json
{
  "source_url": "https://openai.com/careers/some-role/",
  "title": "Some Role",
  "company_name": "OpenAI",
  "location": "San Francisco",
  "role_type": "full-time",
  "description": "...",
  "compensation": "$200K – $300K + Equity"
}
```

## Running tests

```bash
cd backend && make check
```

New tests are in:
- `tests/unit/test_parse_service.py` — unit tests for each adapter and helper
- `tests/contract/test_ingest.py` — existing contract tests (unchanged)

## Adding a new site adapter

1. Open `backend/jobforce/services/parse.py`
2. Add a new adapter dict (translate CSS selectors from `chrome-extension/content.js`)
3. Register it in `SITE_ADAPTERS` keyed by hostname
4. Add unit tests in `tests/unit/test_parse_service.py`
