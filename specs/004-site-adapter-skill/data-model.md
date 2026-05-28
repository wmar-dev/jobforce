# Data Model: Site Adapter Skill

**Feature**: `004-site-adapter-skill` | **Date**: 2026-05-27

## Entities

### FieldSummary

A structured report produced by the skill after inspecting a job posting page.
Consumed only at runtime (printed to the developer, never persisted).

| Field          | Type            | Description                                        |
| -------------- | --------------- | -------------------------------------------------- |
| url            | string          | The URL that was inspected                         |
| hostname       | string          | Extracted hostname (e.g. `openai.com`)             |
| title          | string \| null  | Job title found on the page                        |
| company_name   | string \| null  | Company name found on the page                     |
| location       | string \| null  | Location string found on the page                  |
| description    | string \| null  | Job description body text                          |
| compensation   | string \| null  | Compensation range if present on the page          |
| role_type      | string \| null  | `full-time`, `part-time`, `contract`, `internship` |
| adapter_exists | boolean         | Whether `content.js` already has an entry for this hostname |

### SiteAdapter (JS object in `content.js`)

An object literal registered in the `ADAPTERS` map keyed by hostname.
Each property is a function `(doc) => string | null`.

| Property     | Type                        | Description                                |
| ------------ | --------------------------- | ------------------------------------------ |
| company_name | `(doc) => string \| null`   | Extractor for company name (optional)      |
| location     | `(doc) => string \| null`   | Extractor for job location (optional)      |
| description  | `(doc) => string \| null`   | Extractor for job description body (optional) |
| compensation | `(doc) => string \| null`   | Extractor for compensation range (optional)|
| title        | `(doc) => string \| null`   | Extractor for job title (optional — override generic only if needed) |

Fields are optional: omit any field where the generic adapter already works
reliably for that site. The merge framework fills in omitted fields from the
generic adapter automatically.

### AdapterRegistry (within `content.js`)

The `ADAPTERS` constant — a plain object mapping hostname strings to
`SiteAdapter` objects.

```
hostname (string) → SiteAdapter
```

**Validation rules**:
- Each key MUST be a bare hostname with no `www.` prefix (stripped at runtime).
- Each value MUST only contain field-name keys matching those in `genericAdapter`.
- No two entries may share the same hostname key.

## State Transitions

The skill operates as a linear workflow with one decision branch:

```
START
  └─► Navigate to URL
        ├─► [failure] → Report error, EXIT (no writes)
        └─► [success] → Capture snapshot
              └─► Extract FieldSummary
                    └─► Display FieldSummary to developer
                          └─► Check git status of content.js
                                ├─► [dirty] → Warn developer, EXIT (no writes)
                                └─► [clean] → Generate SiteAdapter JS
                                      └─► Write to content.js (add or replace)
                                            └─► Report completion, EXIT
```
