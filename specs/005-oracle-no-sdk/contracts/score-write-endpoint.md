# Contract: Score Write Endpoint

**Feature**: `005-oracle-no-sdk` | **Date**: 2026-05-27

## Endpoint

```
PATCH /api/jobs/{job_id}
```

Extended from feature 004. Accepts fit score fields in addition to existing
`title`, `location`, `role_type`, `description` fields.

## Request

```json
{
  "fit_score": 0.85,
  "fit_scored": 1,
  "fit_confidence": "high",
  "fit_rationale": "Strong Python background matches core requirements."
}
```

| Field | Type | Required | Constraints |
| --- | --- | --- | --- |
| fit_score | float | No | 0.0 ≤ value ≤ 1.0 |
| fit_scored | int | No | 0 or 1 |
| fit_confidence | string | No | "high", "medium", or "low" |
| fit_rationale | string | No | non-empty string |

All fields are optional (partial update). Omitted fields are not modified.

## Response (200 OK)

Returns the full `JobListingDetail` object (same as `GET /api/jobs/{id}`).

## Error Responses

| Status | Condition |
| --- | --- |
| 404 | Job ID does not exist |
| 422 | fit_score outside 0.0–1.0 range |

## Stub endpoint contract: `POST /api/oracle/rank`

The existing endpoint is retained as a stub returning:

```json
HTTP 501 Not Implemented
{
  "detail": "Oracle ranking is now performed via Claude Code. Run /oracle-rank in Claude Code to score jobs."
}
```

## Skill invocation contract: `/oracle-rank`

```
/oracle-rank [job_id ...]
```

| Argument | Required | Description |
| --- | --- | --- |
| job_id(s) | No | Space-separated IDs; omit to rank all active jobs |

### Skill output (per job)

```
#1  Job #2 — Software Engineer, Ad Formats @ OpenAI
    Score: 85%  Confidence: high
    Rationale: Strong background in systems engineering matches core requirements.

#2  Job #5 — Platform Engineer @ DevCo
    Score: 42%  Confidence: medium
    ⚠ Job description is too sparse for reliable scoring
```

### Skill invariants

- Fetches job data via `GET /api/jobs` (or `GET /api/jobs/{id}` for specific IDs).
- Fetches user profile via `GET /api/profile`.
- Scores each job independently; a failure on one job does not abort others.
- Writes each result via `PATCH /api/jobs/{id}` immediately after scoring.
- Score values are 0.0–1.0; clamped before writing if out of range.
- Backend must be running at `localhost:8000`.
