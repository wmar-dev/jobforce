# API Contracts: Oracle and Forge Use Resume as Candidate Profile

**Branch**: `007-oracle-forge-resume` | **Date**: 2026-05-28

## Changed Endpoints

### POST /api/resume/tailor

**Before**: Accepted `{job_id, base_resume_id}` and called the Anthropic SDK internally to tailor the resume.

**After**: Accepts `{job_id, structured_data}` — the skill performs AI tailoring and sends the result here for storage.

#### Request

```json
{
  "job_id": 42,
  "structured_data": {
    "name": "...",
    "summary": "Tailored summary...",
    "skills": ["..."],
    "experience": [...]
  }
}
```

| Field | Type | Required | Notes |
| ----- | ---- | -------- | ----- |
| job_id | integer | yes | Must match an existing JobListing |
| structured_data | object | yes | Full tailored resume JSON from the skill |

#### Response — 200 OK

```json
{
  "id": 7,
  "label": "Tailored for Senior Engineer",
  "is_base": false,
  "job_listing_id": 42,
  "structured_data": { "..." : "..." },
  "created_at": "2026-05-28T12:00:00Z",
  "updated_at": "2026-05-28T12:00:00Z",
  "diff": [
    { "field": "summary", "original": "\"...\"", "tailored": "\"...\"" }
  ]
}
```

#### Error responses

| Status | Condition |
| ------ | --------- |
| 404 | `job_id` not found |
| 404 | No base resume exists (diff source unavailable) |

---

## Removed Endpoints

### GET /api/profile
### PUT /api/profile

Both removed. Replaced by `GET /api/resume/base` and `PUT /api/resume/base` (unchanged from prior work).

---

## Unchanged Endpoints (referenced by updated skills)

### GET /api/resume/base

Returns the base resume. Used by `/oracle-rank` (Step 3) and `/forge-tailor` (Step 2) in place of the former `/api/profile` call.

```json
{
  "id": 1,
  "label": "Base Resume",
  "is_base": true,
  "job_listing_id": null,
  "structured_data": { "name": "...", "skills": [...], "experience": [...] },
  "created_at": "...",
  "updated_at": "..."
}
```

| Status | Condition |
| ------ | --------- |
| 200 | Base resume exists |
| 404 | No base resume seeded yet |
