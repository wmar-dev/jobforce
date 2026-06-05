# Data Model: Hacker News "Who's Hiring" Parser

## No Schema Changes

This feature adds no new database tables or columns. All extracted data maps to the existing `job_listings` table via the existing `IngestPayload` / `ingest_listing` path.

## Extraction Output Shape

The HN adapter produces a `dict` matching the existing `parse_html` return contract:

| Field          | Source                                         | Nullable |
| -------------- | ---------------------------------------------- | -------- |
| `source_url`   | Input URL (passed through)                     | No       |
| `title`        | Pipe token [1] if `|` in first line            | Yes      |
| `company_name` | Pipe token [0] if `|` in first line; else first non-empty line fragment | No |
| `location`     | Pipe token [2] if `|` in first line; else null | Yes      |
| `role_type`    | Scanned from all pipe tokens; else `_generic_role_type` fallback | Yes |
| `description`  | Full `.commtext` HTML → markdownify            | Yes      |

## `hn_thread` CLI Output

Stdout: JSON array of strings. Each string is a canonical HN comment URL.

```
["https://news.ycombinator.com/item?id=<N>", ...]
```

Stderr: progress/error messages (not parsed by caller).
Exit code: 0 on success, 1 on HTTP error or invalid thread URL.

## Entities

**HN Comment** (transient, not persisted):
- `comment_id`: str — HN item ID (from URL or `tr[id]`)
- `commtext_el`: BeautifulSoup Tag — the `.commtext` div
- `first_line`: str — first text line of the comment body
- `has_pipe`: bool — whether `|` appears in `first_line`
- `tokens`: list[str] — pipe-split tokens of `first_line` (only when `has_pipe`)

**HN Thread** (transient, used by `hn_thread` CLI only):
- `thread_id`: str — HN item ID from thread URL
- `comment_ids`: list[str] — top-level comment IDs (dead/flagged excluded)
