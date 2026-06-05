# Contract: `hn_thread` CLI

## Invocation

```bash
python -m jobforce.cli.hn_thread <thread_url>
```

## Input

| Argument     | Type   | Required | Description |
| ------------ | ------ | -------- | ----------- |
| `thread_url` | string | Yes      | Full URL of an HN "Who's Hiring" thread, e.g. `https://news.ycombinator.com/item?id=48357725` |

## Output (stdout)

JSON array of canonical comment URLs, one per top-level non-dead comment:

```json
["https://news.ycombinator.com/item?id=48408037", "https://news.ycombinator.com/item?id=48358328"]
```

- Empty array `[]` if thread has no eligible comments
- Each URL is a string suitable for passing directly to `scout_fetch --url`

## Exit Codes

| Code | Meaning |
| ---- | ------- |
| 0    | Success — JSON array written to stdout |
| 1    | Error — invalid URL, non-HN hostname, HTTP failure, or HTML parse error |

## Stderr

Human-readable progress/error messages. Not parsed by callers.

Examples:
```
[hn_thread] fetching https://news.ycombinator.com/item?id=48357725
[hn_thread] found 286 top-level comments
[hn_thread] error: HTTP 429 Too Many Requests
```

## Contract: `parse_html` for HN URLs

The existing `parse_html(html, url)` function routes `news.ycombinator.com` URLs through the new HN adapter. Return shape is identical to all other adapters:

```python
{
    "source_url": str,        # input url
    "title": str | None,
    "company_name": str | None,
    "location": str | None,
    "role_type": str | None,  # "full-time" | "part-time" | "contract" | "internship" | None
    "description": str | None,  # markdown
}
```
