# Contract: Business Error Codes

Every business-rule error returns this body, with the HTTP status listed below:

```json
{ "detail": "<human-readable message, unchanged from today>", "code": "<ErrorCode>" }
```

Input-validation errors (bad types, missing required fields) are unchanged. They are FastAPI's `HTTPValidationError` body, `{"detail": [{"loc": [...], "msg": "...", "type": "..."}]}`, with **no** `code`. Consumers tell the two 422 shapes apart by whether `code` is present.

## Catalog (`jobforce/routers/errors.py::ErrorCode`)

| Code | Status | `detail` (exact, unchanged) | Raised by |
| --- | --- | --- | --- |
| `JOB_NOT_FOUND` | 404 | `Job listing not found` | `GET/PATCH/DELETE /jobs/{id}`, `POST /jobs/{id}/reparse`, `PATCH /jobs/{id}/status`, `GET/PUT/DELETE /jobs/{id}/note`, `POST /resume/tailor`, `POST /coach/prep`, `GET /coach/jobs/{id}/latest-session` |
| `NOTE_NOT_FOUND` | 404 | `Note not found` | `GET /jobs/{id}/note`, `DELETE /jobs/{id}/note` |
| `SNAPSHOT_NOT_FOUND` | 404 | `No HTML snapshot stored for this job` | `POST /jobs/{id}/reparse` |
| `INVALID_TRANSITION` | 422 | *(message from the state machine)* | `PATCH /jobs/{id}/status` |
| `MISSING_COMPANY_ID` | 422 | `all_active/saved_only requires company_id` | `POST /jobs/bulk-archive` |
| `CONFLICTING_OPTIONS` | 422 | `all_active and saved_only are mutually exclusive` | `POST /jobs/bulk-archive` |
| `COMPANY_NOT_FOUND` | 404 | `Company not found` | `GET/PATCH /companies/{id}`, `POST /companies/{id}/merge`, `GET/POST /companies/{id}/notes` |
| `SELF_MERGE` | 422 | `Cannot merge a company into itself` | `POST /companies/{id}/merge` |
| `BASE_RESUME_MISSING` | 404 | `No base resume found — add config/resume.json` | `GET /resume/base`, `POST /resume/tailor`, `POST /resume/{id}/export` |
| `RESUME_NOT_FOUND` | 404 | `Resume not found` | `POST /resume/{id}/export` |
| `RANK_RESULT_NOT_FOUND` | 404 | `No ranking result found for this job` | `GET /oracle/rank/{job_id}` |
| `RANKING_MOVED_TO_SKILL` | 501 | `Oracle ranking is now performed via Claude Code. …` | `POST /oracle/rank` (deprecated) |
| `PREP_SESSION_NOT_FOUND` | 404 | `No prep session found for this job` | `GET /coach/jobs/{id}/latest-session` |
| `SESSION_NOT_FOUND` | 404 | `Interview session {id} not found` | `POST /coach/sessions/{id}/answer`, `GET /coach/sessions/{id}/summary` |
| `QUESTION_NOT_FOUND` | 404 | `Question {qid} not found in session {id}` | `POST /coach/sessions/{id}/answer` |

The exact raise sites are confirmed during implementation by grepping for `HTTPException` / `JSONResponse(` in `routers/`. After migration, `grep -rn "HTTPException(" backend/jobforce/routers/` must return zero results.

## Rules

1. Adding a code: add the enum member and its status in `ErrorCode`, use it in an `ApiError` raise, list it in that route's `error_responses(...)`, and regenerate the spec.
2. Codes are never renamed or reused for a different meaning; they are part of the contract.
3. `detail` text may be improved later, but consumers MUST branch on `code`, never on `detail`.
4. `SESSION_NOT_FOUND` and `QUESTION_NOT_FOUND` both come from `ValueError` in `services/coach.py` today. The service will raise two distinct `LookupError` subclasses so the router can map each to its own code without parsing messages.
