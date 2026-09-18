# Feature Specification: Improve Test Coverage for Jobs Router and Coach Service

**Feature Branch**: `014-improve-test-coverage`

**Created**: 2026-09-17

**Status**: Draft

**Input**: User description: "Fix Backend routers/jobs.py at 62% with large uncovered blocks (business logic, not boilerplate) and services/coach.py at 48% (expected somewhat, mid-migration per feature 011 — evaluate_answer is a stub)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Job list filtering and sorting is verified (Priority: P1)

The maintainer relies on the job listing feed (filtered by company, score, location, role, status, free-text search, and sorted every which way) on nearly every visit to the dashboard and in almost every skill (Oracle, Scout, Forge) that reads jobs. A silent regression here — a filter that stops filtering, a sort that breaks ties wrong, a note flag that's always false — would be hard to notice and would quietly corrupt the job search workflow.

**Why this priority**: This is the single most-exercised code path in the backend; nearly every other feature depends on `GET /api/jobs` returning correct results.

**Independent Test**: Can be fully tested by seeding jobs with varied companies/scores/statuses/notes and asserting `GET /api/jobs` returns the right subset and order for each filter/sort combination, independent of any other endpoint.

**Acceptance Scenarios**:

1. **Given** jobs from multiple companies with different fit scores and statuses, **When** `GET /api/jobs` is called with `company`, `min_score`, `fit_scored`, `location`, `role_type`, `title`, or `q` filters (individually and combined), **Then** only matching, non-default-excluded jobs are returned.
2. **Given** jobs with and without a `NOT NULL` `fit_score` and with and without an associated note, **When** `GET /api/jobs` is sorted by each supported column in both directions, **Then** results are ordered correctly with nulls last and `has_note` correctly reflects note presence.

---

### User Story 2 - Job detail lifecycle and pipeline transitions are verified (Priority: P1)

The maintainer moves jobs through the pipeline (save → shortlist → applied → rejected, etc.) daily via `PATCH /api/jobs/{id}/status`, and edits or removes individual listings via the detail, patch, and delete endpoints. An unverified regression in the status state machine, the 404 handling, or the field-patch logic could silently corrupt pipeline history or destroy data.

**Why this priority**: `PATCH /api/jobs/{id}/status` is called out in CLAUDE.md as "the only way to change a job's pipeline status" and is the backbone of the `/scout-reject` skill and manual pipeline management; correctness here is critical.

**Independent Test**: Can be fully tested by seeding a single job and exercising `GET`, `PATCH`, `DELETE /api/jobs/{id}` and `PATCH /api/jobs/{id}/status` against it (existing and missing IDs, valid and invalid status transitions) independent of the list endpoint.

**Acceptance Scenarios**:

1. **Given** an existing job, **When** `GET /api/jobs/{id}` is called, **Then** the response includes full detail and status history; **When** called with a non-existent ID, **Then** a 404 is returned.
2. **Given** an existing job, **When** `PATCH /api/jobs/{id}` supplies a subset of fields, **Then** only those fields change and the rest are preserved in the returned detail.
3. **Given** an existing job, **When** `DELETE /api/jobs/{id}` is called, **Then** the job is removed; calling it again returns 404.
4. **Given** an existing job in a given status, **When** `PATCH /api/jobs/{id}/status` is called with a valid next status, **Then** the transition is recorded and returned; **When** called with an invalid next status, **Then** a 422 with `code: "INVALID_TRANSITION"` is returned; **When** called for a non-existent job, **Then** a 404 is returned.

---

### User Story 3 - Recruiter notes CRUD is verified (Priority: P2)

The maintainer attaches a single free-text recruiter note per job (via `GET`/`PUT`/`DELETE /api/jobs/{id}/note`) to track recruiter call context. Losing or silently failing to persist a note edit would erase context that isn't recoverable from anywhere else.

**Why this priority**: Frequently used but lower blast-radius than pipeline status or listing correctness — a note bug loses context, it doesn't corrupt the pipeline state or the job feed.

**Independent Test**: Can be fully tested by seeding a job with no note, then exercising create (first `PUT`), read, update (second `PUT`), and delete against its note endpoint independent of other job fields.

**Acceptance Scenarios**:

1. **Given** a job with no note, **When** `GET /api/jobs/{id}/note` is called, **Then** a 404 is returned.
2. **Given** a job with no note, **When** `PUT /api/jobs/{id}/note` is called, **Then** a note is created and returned; **When** `PUT` is called again with different text, **Then** the existing note is updated in place (not duplicated).
3. **Given** a job with a note, **When** `DELETE /api/jobs/{id}/note` is called, **Then** the note is removed and a subsequent `GET` returns 404.
4. **Given** a non-existent job ID, **When** any note endpoint is called, **Then** a 404 is returned.

---

### User Story 4 - Job re-parsing from stored snapshots is verified (Priority: P2)

After fixing or adding a site adapter, the maintainer re-extracts `title`, `location`, `role_type`, and `description` for already-ingested jobs via `POST /api/jobs/{id}/reparse` instead of re-crawling. An unverified regression here would leave stale or corrupted fields after an adapter fix, defeating the endpoint's purpose.

**Why this priority**: Used less often than listing/status/notes (only after adapter changes), but is explicitly documented in CLAUDE.md as the sanctioned way to refresh ingested data, so its two failure modes (missing job, missing snapshot) and its success path need explicit verification.

**Independent Test**: Can be fully tested by seeding a job with and without a stored HTML snapshot and calling `POST /api/jobs/{id}/reparse`, independent of the crawling/ingest pipeline.

**Acceptance Scenarios**:

1. **Given** a job with a stored HTML snapshot, **When** `POST /api/jobs/{id}/reparse` is called, **Then** `title`, `location`, `role_type`, and `description` are updated from the current site adapter's extraction and the refreshed detail is returned.
2. **Given** a job with no stored snapshot, **When** `POST /api/jobs/{id}/reparse` is called, **Then** a 404 is returned.
3. **Given** a non-existent job ID, **When** `POST /api/jobs/{id}/reparse` is called, **Then** a 404 is returned.

---

### User Story 5 - Coach prep-session persistence is verified (Priority: P3)

Since feature 011, the coach-prep skill generates interview questions itself and hands them to the backend purely to store and later retrieve; the backend performs no AI reasoning. The maintainer needs confidence that a generated prep pack is durably saved and retrievable, and that the answer-evaluation stub and session summary behave predictably now that AI evaluation is out of scope.

**Why this priority**: Used only when running interview prep, and the underlying logic is now simple storage/retrieval (no AI call), so it carries lower risk than the job-pipeline paths — but it's currently the least-covered code in the backend and worth locking down before further coach work resumes.

**Independent Test**: Can be fully tested by seeding an interview session with a known question list and asserting persistence, evaluation-stub, and summary-retrieval behavior, independent of the jobs endpoints.

**Acceptance Scenarios**:

1. **Given** a list of interview questions for a job, **When** a prep pack is stored, **Then** it is persisted as an interview session and returned with a generated session ID alongside the original questions.
2. **Given** a stored session and a question ID that exists in it, **When** an answer is evaluated, **Then** the stub feedback and a 0.0 score are returned; **When** the question ID does not exist in the session, or the session ID does not exist, **Then** an error is raised.
3. **Given** a stored session with a previously saved overall summary, **When** the session summary is requested, **Then** the saved summary is returned; **given** a session with no summary (or a malformed one), **when** the summary is requested, **then** a well-formed default summary (zero score, empty improvement list, placeholder message) is returned instead of an error.

---

### Edge Cases

- What happens when `GET /api/jobs` filters combine to match zero jobs (e.g., a `min_score` above every job's score)? The response must still be a well-formed page with `total: 0` and an empty `items` list, not an error.
- How does `POST /api/jobs/bulk-archive` behave when `all_active`/`saved_only` is set but `company_id` is omitted, or when both flags are set together? Both must return 422 without archiving anything.
- How does `POST /api/jobs/bulk-archive` behave for a company with zero eligible jobs? It must return `archived_count: 0`, not an error.
- What happens on reparse when the site adapter extracts only some of the four fields (e.g., no `location`)? Only the fields the adapter actually returned should change; the rest must be left untouched.
- What happens when `evaluate_answer` is called against a session whose stored `questions` list is empty? It must raise the same "question not found" error as any other unmatched question ID, not crash on an empty list.
- What happens when `get_session_summary_data`'s stored `overall_summary` is present but is not valid JSON? The default summary must be returned instead of propagating a parse error.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Test suite MUST verify that `GET /api/jobs` applies each optional filter (`company_id`, `company` substring, `fit_scored`, `min_score`, `location`, `role_type`, `title` substring, `q` description substring, `source_url`) both individually and in combination, returning only matching listings.
- **FR-002**: Test suite MUST verify that `GET /api/jobs` sorts correctly for every supported `sort_by` value (`fit_score`, `created_at`, `title`, `status`, `company`) in both `asc` and `desc` directions, including that null-valued sort columns are ordered last and that ties break by `created_at desc`.
- **FR-003**: Test suite MUST verify that `GET /api/jobs` correctly sets `has_note: true` for listings with an associated recruiter note and `false` for listings without one.
- **FR-004**: Test suite MUST verify `POST /api/jobs/bulk-archive` rejects `all_active`/`saved_only` without `company_id` (422), rejects both flags set together (422), and returns the correct `archived_count` for each of the default, `all_active`, and `saved_only` modes.
- **FR-005**: Test suite MUST verify `GET /api/jobs/{id}` returns full detail with ordered status history for an existing job and a 404 for a non-existent one.
- **FR-006**: Test suite MUST verify `PATCH /api/jobs/{id}` updates only the fields supplied in the request body, leaves omitted fields unchanged, and returns a 404 for a non-existent job.
- **FR-007**: Test suite MUST verify `DELETE /api/jobs/{id}` removes an existing job and returns a 404 for a non-existent job (including on a repeated delete).
- **FR-008**: Test suite MUST verify `POST /api/jobs/{id}/reparse` re-extracts `title`, `location`, `role_type`, and `description` from a stored HTML snapshot via the current site adapter, and returns a 404 when the job or its stored snapshot does not exist.
- **FR-009**: Test suite MUST verify `PATCH /api/jobs/{id}/status` returns the recorded transition on a valid status change, returns a 422 with `code: "INVALID_TRANSITION"` on a disallowed one, and returns a 404 for a non-existent job.
- **FR-010**: Test suite MUST verify `GET`, `PUT`, and `DELETE /api/jobs/{id}/note` create, retrieve, update-in-place, and remove a job's single recruiter note, and return a 404 for a non-existent job or a non-existent note.
- **FR-011**: Test suite MUST verify that storing a prep pack persists the given question list as an interview session and returns it together with the generated session ID.
- **FR-012**: Test suite MUST verify that evaluating an answer raises an error for an unknown session ID or an unknown question ID within a known session, and returns the stub feedback message with a 0.0 score for a known question.
- **FR-013**: Test suite MUST verify that requesting a session summary returns the previously stored summary when present and valid, and a well-formed default summary (0.0 score, placeholder message, empty improvement list) when the stored summary is absent or fails to parse.
- **FR-014**: All new and existing tests MUST pass together under the project's standard test/quality gate, with no reduction in coverage for any other currently-covered module.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Line coverage for `backend/jobforce/routers/jobs.py` reaches at least 85%, up from the current 62%.
- **SC-002**: Line coverage for `backend/jobforce/services/coach.py` reaches at least 85%, up from the current 48%.
- **SC-003**: Every distinct success and error path enumerated in this spec's acceptance scenarios (404s, the 422 `INVALID_TRANSITION` response, the two bulk-archive 422 validation errors, and the coach evaluation/summary error and default-fallback paths) has at least one passing test that exercises it.
- **SC-004**: The full backend test/quality gate passes with zero regressions to previously-passing tests after the new tests are added.

## Assumptions

- This feature is test-only: it adds test coverage for existing, already-shipped behavior in `routers/jobs.py` and `services/coach.py`. It does not change any API contract, add endpoints, or alter business logic — if a test uncovers an actual bug, that fix is out of scope for this spec and should be tracked separately.
- The 85% coverage target (SC-001, SC-002) is a reasonable default chosen to match the coverage level already achieved by comparable service modules in this codebase (e.g. `services/scout.py` at 85%, `services/storage.py` at 82%), since no project-wide minimum coverage threshold is currently configured.
- `evaluate_answer` in `services/coach.py` remains an intentional stub per the completed feature-011 migration (AI reasoning now lives in the `coach-prep` skill, not the backend); this spec covers the stub's existing deterministic behavior (raise on not-found, fixed feedback/score on success) and does not add or test any AI evaluation logic.
- Existing test infrastructure (the async test client and DB fixtures already used under `backend/tests/`) is reused as-is; no new test tooling or fixtures framework is introduced.
- The frontend and Chrome extension are unaffected and out of scope, since both target modules are backend-only.
