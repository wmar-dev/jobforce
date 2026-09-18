# Data Model: Improve Test Coverage for Jobs Router and Coach Service

No schema changes. This feature adds tests against the existing entities below (see
`backend/jobforce/db/models.py` for full definitions); only the fields and relationships exercised by the
new tests are listed.

## JobListing

The subject of every `routers/jobs.py` endpoint under test.

- `status`: pipeline stage (`saved`, `shortlisted`, `applied`, `rejected`, `archived`, `withdrawn`, ...).
  Transitions are validated against `services/scout.py::_VALID_TRANSITIONS`; tests must exercise at least one
  valid and one invalid transition per acceptance scenario in User Story 2.
- `fit_score` / `fit_scored`: nullable float / boolean flag written by the Oracle skill. Tests need jobs with
  a null score, a low score, and a high score to exercise `min_score` filtering and null-last sort ordering.
- `company_id` → **Company**: needed for `company_id` exact-match and `company` substring filter tests.
- Relationship to **StatusTransition** (`status_history`, one-to-many): needed to assert ordered transition
  history in `GET /api/jobs/{id}`.
- Relationship to **MeetingNote** (one-to-one in practice): needed for the `has_note` flag in list responses
  and for the note CRUD endpoints.

## Company

- `name`: needed for the `company` substring filter and `company` sort tests.

## MeetingNote

- One row per `job_listing_id` (upsert semantics: `PUT` creates if absent, updates in place if present).
  Tests must assert a second `PUT` updates the existing row rather than creating a duplicate.

## InterviewSession

The subject of `services/coach.py` under test.

- `questions`: JSON-encoded list, written by `store_prep_pack`, read back by `evaluate_answer`. Tests need a
  session with a non-empty question list (for the found/not-found question-id branches) and, per the Edge
  Cases in spec.md, a session with an *empty* question list (to confirm the not-found branch still raises
  cleanly rather than erroring on an empty sequence).
- `overall_summary`: nullable JSON-encoded string. **Not written by any current code path** — tests for the
  "summary present" and "summary present but malformed" branches of `get_session_summary_data` must seed this
  column directly via the `db_session` fixture (see research.md Decision 2).

## StatusTransition

- `from_status` / `to_status` / `transitioned_at`: read-only from the test's perspective; asserted for
  ordering and correctness after a `PATCH /api/jobs/{id}/status` call.
