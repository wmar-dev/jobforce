# Quickstart: HN "Who's Hiring" Parser

## Capture a single HN job comment

```bash
cd backend && uv run python -m jobforce.cli.scout_fetch --url "https://news.ycombinator.com/item?id=48408037"
```

## Extract all comment URLs from a thread

```bash
cd backend && uv run python -m jobforce.cli.hn_thread "https://news.ycombinator.com/item?id=48357725"
```

Outputs a JSON array of comment URLs.

## Bulk-ingest a full thread via scout-companies

Add the thread URL as a `careers_url` in `config.yaml`:

```yaml
search:
  target_companies:
    - name: "Hacker News Who's Hiring (June 2026)"
      domain: ""
      careers_url: "https://news.ycombinator.com/item?id=48357725"
```

Then run `/scout-companies` — it detects the HN hostname, calls `hn_thread` to get comment URLs, and ingests each via `scout_fetch`.

## Run tests

```bash
cd backend && uv run pytest tests/unit/test_parse_service.py tests/unit/test_hn_thread.py -v
```

## Check all quality gates

```bash
cd backend && make check
```
