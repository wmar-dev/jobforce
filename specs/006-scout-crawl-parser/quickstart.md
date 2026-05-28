# Quickstart: Scout Crawl Deterministic Parser

## Setup (one-time)

```bash
cd backend
uv sync
uv run playwright install chromium
```

## Running the parser directly

```bash
cd backend
uv run python -m jobforce.cli.scout_fetch --url "https://openai.com/careers/some-role/"
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
cd backend && uv run python -m pytest tests/unit/test_parse_service.py tests/unit/test_scout_fetch.py -v
```

## Adding a new site adapter

1. Open `backend/jobforce/services/parse.py`
2. Add field extractor functions (translate CSS selectors from `chrome-extension/content.js`)
3. Register the adapter in `SITE_ADAPTERS` keyed by hostname (e.g., `"greenhouse.io"`)
4. Add a fixture file in `backend/tests/fixtures/<site>_job.html`
5. Add unit tests in `backend/tests/unit/test_parse_service.py`

## Fixture files

Static HTML fixtures for unit tests (no live network calls):

- `backend/tests/fixtures/openai_job.html` — OpenAI adapter tests
- `backend/tests/fixtures/generic_job.html` — Generic adapter tests
