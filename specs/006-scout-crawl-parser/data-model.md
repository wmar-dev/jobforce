# Data Model: Scout Crawl Deterministic Parser

No new database tables or schema changes are required. This feature adds parsing logic that feeds the existing `IngestPayload` model.

## ParseResult (in-process struct)

Produced by `services/parse.py` and consumed by the scout-crawl skill's ingest POST call. Not persisted independently — it becomes the `IngestPayload`.

| Field | Type | Source |
|---|---|---|
| `source_url` | `str` | Passed in (original URL) |
| `title` | `str` | Adapter extraction |
| `company_name` | `str` | Adapter extraction |
| `location` | `str \| None` | Adapter extraction |
| `role_type` | `"full-time" \| "part-time" \| "contract" \| "internship" \| None` | Adapter extraction |
| `description` | `str \| None` | Adapter extraction |
| `compensation` | `str \| None` | Adapter extraction (site-specific only) |

## Adapter Registry (in-memory)

| Name | Key | Fallback |
|---|---|---|
| Generic adapter | `None` (always runs) | — |
| OpenAI adapter | `"openai.com"` | Generic |

## CLI Interface (parse_job.py)

Input: `--url <str>` and `--html-file <path>`  
Output: JSON on stdout matching `ParseResult` fields above  
Exit code: `0` on success, `1` on parse error
