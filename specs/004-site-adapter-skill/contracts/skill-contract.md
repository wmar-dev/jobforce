# Contract: `/site-adapter-update` Skill

**Feature**: `004-site-adapter-skill` | **Date**: 2026-05-27

## Invocation

```
/site-adapter-update <url>
```

| Parameter | Required | Description                                    |
| --------- | -------- | ---------------------------------------------- |
| `url`     | Yes      | Full URL of a publicly accessible job posting  |

## Outputs

### 1. Field Summary (always produced on success)

Printed to the developer before any code change:

```
## Field Summary: <hostname>

| Field        | Value                        |
| ------------ | ---------------------------- |
| title        | <value or "(not found)">     |
| company_name | <value or "(not found)">     |
| location     | <value or "(not found)">     |
| description  | <truncated to 200 chars>...  |
| compensation | <value or "(not found)">     |
| role_type    | <value or "(not found)">     |

Adapter exists: <Yes / No>
```

### 2. Updated `chrome-extension/content.js`

The `ADAPTERS` object in the file is updated with a new or replaced entry
for the target hostname. All other content is unchanged.

### 3. Completion report

```
✅ Adapter written for <hostname>
   File: chrome-extension/content.js
   Fields with site-specific extractors: <list>
   Fields falling back to generic: <list>
```

## Error Responses

| Condition                        | Output                                                    | Action   |
| -------------------------------- | --------------------------------------------------------- | -------- |
| No URL argument provided         | `❌ Usage: /site-adapter-update <url>`                    | Exit     |
| Page navigation fails            | `❌ Could not load <url>: <reason>`                       | Exit     |
| Page appears to be non-job page  | `⚠️ Page may not be a job posting. Field summary shown — proceed? (y/n)` | Pause |
| content.js has uncommitted edits | `⚠️ content.js has uncommitted changes. Commit or stash them first.` | Exit |
| Cannot locate ADAPTERS in file   | `❌ Could not find ADAPTERS object in content.js`         | Exit     |

## Invariants

- The skill MUST NOT make any changes to `content.js` before the field summary
  is shown and the git guard passes.
- The generic adapter, `runAdapter` function, `merge` function, message
  listener, and module exports in `content.js` MUST remain byte-for-byte
  identical after the skill runs.
- Running the skill twice on the same URL MUST be idempotent — the second run
  replaces the adapter written by the first run; no duplicate entry is created.
