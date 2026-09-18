---
description: "Task list for feature implementation"
---

# Tasks: Improve Test Coverage for Jobs Router and Coach Service

**Input**: Design documents from `/specs/014-improve-test-coverage/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: This feature's functional requirements are literally "the test suite MUST verify X" — the test
tasks below **are** the implementation. There is no separate non-test code being written except the one-line
coverage-config fix in Phase 2.

**Organization**: Tasks are grouped by user story (spec.md priorities P1/P1/P2/P2/P3), each independently
testable and independently valuable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- All file paths below are relative to the repository root

## Important: verified, minimal target list

Every "missing line" cited below was confirmed empirically (not guessed) by running coverage with the
Phase 2 fix applied and cross-referencing against the tests that already exist in
`backend/tests/contract/test_jobs.py`, `backend/tests/contract/test_coach.py`, and
`backend/tests/contract/test_oracle.py`. Several branches that line numbers alone would suggest are
uncovered turned out to already be exercised by tests in *other* files (e.g. `PATCH /api/jobs/{id}`'s
happy path is covered by `test_oracle.py`, which is why only its 404 branch remains). Do not add tests for
anything not listed here — it would be redundant with what already passes.

---

## Phase 1: Setup

- [X] T001 Run `cd backend && uv sync` to confirm the test environment (pytest, pytest-asyncio, pytest-cov,
  httpx) is installed and up to date. No file changes expected; this only validates the environment before
  Phase 2's config edit.

**Checkpoint**: Environment confirmed ready.

---

## Phase 2: Foundational (Blocking Prerequisite)

**⚠️ CRITICAL**: No user-story task below should be started until this phase's re-baseline is confirmed —
otherwise you will waste effort writing tests for lines that are already covered.

- [X] T002 In `backend/pyproject.toml`, add `concurrency = ["greenlet", "thread"]` to the
  `[tool.coverage.run]` section (it currently only has `omit = ["tests/*"]`). This makes `coverage.py`
  follow SQLAlchemy's async-to-sync `greenlet` bridge instead of silently under-counting lines that execute
  after an `await session.commit()`/`refresh()`/`get()` call (see research.md Decision 1).
- [X] T003 Re-run `cd backend && rm -f .coverage && uv run pytest --cov=jobforce.routers.jobs --cov=jobforce.services.coach --cov-report=term-missing tests/ -q`
  and confirm the report now shows:
  - `jobforce/routers/jobs.py` ~92%, missing lines `141, 179, 182, 184, 190, 192, 301, 328-332, 348, 370, 393, 414, 447`
  - `jobforce/services/coach.py` ~76%, missing lines `46, 50, 66, 71-75`
  If the numbers or missing-line list differ meaningfully from this, stop and re-investigate (see
  quickstart.md Step 1) before starting Phase 3 — the task list below targets these exact lines.

**Checkpoint**: True baseline established. Every task below closes one or more of the specific lines listed
in T003.

---

## Phase 3: User Story 1 — Job list filtering and sorting (Priority: P1) 🎯 MVP

**Goal**: `GET /api/jobs` correctly applies every filter and sort option, and correctly flags `has_note`.

**Independent Test**: Seed jobs with varied companies/scores/statuses/notes and call `GET /api/jobs` with
each filter/sort combination in isolation; no other endpoint needs to be touched.

All tasks in this phase edit `backend/tests/contract/test_jobs.py` and must be applied **sequentially**
(same file).

- [X] T004 [US1] Add `test_get_jobs_filter_by_company_id` to `backend/tests/contract/test_jobs.py`: seed
  two `Company` rows each with a job, call `GET /api/jobs?company_id=<id>`, assert only that company's job
  is returned (closes line 179).
- [X] T005 [US1] Add `test_get_jobs_filter_by_fit_scored` to `backend/tests/contract/test_jobs.py`: seed one
  job with `fit_scored=1` and one with `fit_scored=0`, assert `?fit_scored=true` and `?fit_scored=false`
  each return only the matching job (closes line 182).
- [X] T006 [US1] Add `test_get_jobs_filter_by_min_score` to `backend/tests/contract/test_jobs.py`: seed jobs
  with `fit_score` `0.3` and `0.8`, assert `?min_score=0.5` returns only the `0.8` job (closes line 184).
- [X] T007 [US1] Add `test_get_jobs_filter_by_title_substring` to `backend/tests/contract/test_jobs.py`:
  seed jobs with distinct titles, assert `?title=<substring>` (mixed case) returns only the matching job
  (closes line 190).
- [X] T008 [US1] Add `test_get_jobs_filter_by_description_substring` to `backend/tests/contract/test_jobs.py`:
  seed jobs with distinct descriptions, assert `?q=<substring>` (mixed case) returns only the matching job
  (closes line 192).
- [X] T009 [US1] Add `test_get_jobs_sort_by_company_without_company_filter` to
  `backend/tests/contract/test_jobs.py`: seed jobs across ≥2 companies, call
  `GET /api/jobs?sort_by=company&sort_dir=asc` with **no** `company` filter, assert results are ordered by
  company name (closes line 141 — the join-for-sort-only branch in `_apply_company_filter`).
- [X] T010 [US1] Add `test_get_jobs_combined_filters_and_sort` to `backend/tests/contract/test_jobs.py`:
  seed jobs varying company, score, and status; call `GET /api/jobs` with `company`, `min_score`, and
  `status` filters combined plus `sort_by=fit_score&sort_dir=desc`; assert the returned set and order are
  correct (spec.md User Story 1, Acceptance Scenario 1).
- [X] T011 [US1] Add `test_get_jobs_sort_nulls_last_and_tiebreak` to `backend/tests/contract/test_jobs.py`:
  seed one job with `fit_score=None` and two others with distinct scores; assert the null-score job sorts
  last for both `sort_dir=asc` and `sort_dir=desc` on `sort_by=fit_score`. Also seed two jobs with equal
  `fit_score` but different `created_at`; assert the more recent one appears first when `sort_dir=desc`
  (spec.md User Story 1, Acceptance Scenario 2 — tie-break by `created_at desc`).

**Checkpoint**: `GET /api/jobs` filtering, sorting, and `has_note` are independently verified end to end.

---

## Phase 4: User Story 2 — Job detail lifecycle and pipeline transitions (Priority: P1)

**Goal**: `GET`/`PATCH`/`DELETE /api/jobs/{id}` and `PATCH /api/jobs/{id}/status` behave correctly for both
existing and missing jobs.

**Independent Test**: Seed a single job and exercise each of these four endpoints against it (existing and
missing IDs), independent of the list endpoint.

All tasks in this phase edit `backend/tests/contract/test_jobs.py` and must be applied **sequentially**
(same file; also sequential after Phase 3's edits to the same file).

- [X] T012 [US2] Add `test_patch_job_not_found_returns_404` to `backend/tests/contract/test_jobs.py`:
  `PATCH /api/jobs/99999` with a valid body (e.g. `{"location": "Remote"}`) returns 404 (closes line 301).
  Note: the happy path of this endpoint is already covered by `tests/contract/test_oracle.py`, which is why
  only the 404 branch is missing.
- [X] T013 [US2] Add `test_patch_job_updates_only_supplied_fields` to `backend/tests/contract/test_jobs.py`:
  seed a job, `PATCH /api/jobs/{id}` with only `{"location": "New York"}`, assert `location` changed and
  `title` (and other untouched fields) are unchanged in the response (spec.md User Story 2, Acceptance
  Scenario 2).
- [X] T014 [US2] Add `test_delete_job_removes_job` to `backend/tests/contract/test_jobs.py`: seed a job,
  `DELETE /api/jobs/{id}` returns 204, then `GET /api/jobs/{id}` returns 404 (closes the success half of
  lines 328–332; this endpoint currently has zero test coverage of any kind).
- [X] T015 [US2] Add `test_delete_job_not_found_returns_404` to `backend/tests/contract/test_jobs.py`:
  `DELETE /api/jobs/99999` returns 404; calling it again also returns 404 (closes the 404 half of lines
  328–332; spec.md User Story 2, Acceptance Scenario 3).
- [X] T016 [US2] Add `test_patch_job_status_not_found_returns_404` to `backend/tests/contract/test_jobs.py`:
  `PATCH /api/jobs/99999/status` with `{"status": "applied"}` returns 404 (closes line 370 — distinct from
  the existing invalid/backward-transition 422 tests, which all use a real job).

**Checkpoint**: Job detail GET/PATCH/DELETE and status-transition success/422/404 paths are all
independently verified.

---

## Phase 5: User Story 3 — Recruiter notes CRUD (Priority: P2)

**Goal**: `GET`/`PUT`/`DELETE /api/jobs/{id}/note` correctly distinguish "job not found" from "note not
found."

**Independent Test**: Seed a job with no note and exercise create/read/update/delete against its note
endpoint, independent of other job fields.

All tasks in this phase edit `backend/tests/contract/test_jobs.py` and must be applied **sequentially**
(same file; also sequential after Phases 3–4's edits to the same file).

- [X] T017 [US3] Add `test_get_job_note_not_found_job_returns_404` to `backend/tests/contract/test_jobs.py`:
  `GET /api/jobs/99999/note` returns 404 (closes line 393). Distinct from the existing
  `test_get_job_note_returns_404_when_no_note`, which uses a real job that simply has no note yet.
- [X] T018 [US3] Add `test_put_job_note_not_found_job_returns_404` to `backend/tests/contract/test_jobs.py`:
  `PUT /api/jobs/99999/note` with `{"body": "..."}` returns 404 (closes line 414).
- [X] T019 [US3] Add `test_delete_job_note_not_found_job_returns_404` to
  `backend/tests/contract/test_jobs.py`: `DELETE /api/jobs/99999/note` returns 404 (closes line 447).
  Distinct from the existing `test_delete_job_note_on_missing_note_returns_404`, which uses a real job with
  no note.

**Checkpoint**: Every note endpoint now distinguishes a missing job from a missing note.

---

## Phase 6: User Story 4 — Job re-parsing from stored snapshots (Priority: P2)

**Goal**: `POST /api/jobs/{id}/reparse` correctly distinguishes "job not found" from "snapshot not found."

**Independent Test**: Seed a job with and without a stored HTML snapshot and call the reparse endpoint,
independent of the crawl/ingest pipeline.

- [X] T020 [US4] Add `test_reparse_job_not_found_returns_404` to `backend/tests/contract/test_jobs.py`
  (sequential after Phases 3–5's edits to the same file): `POST /api/jobs/99999/reparse` returns 404
  (closes line 348). Distinct from the existing `test_reparse_with_no_snapshot_row_returns_404` and
  `test_reparse_with_empty_snapshot_blob_returns_404`, both of which use a real job whose *snapshot* is
  missing/empty.

**Checkpoint**: Reparse's job-missing, snapshot-missing, and success paths are all independently verified.

---

## Phase 7: User Story 5 — Coach prep-session persistence (Priority: P3)

**Goal**: `evaluate_answer`'s error paths and `get_session_summary_data`'s stored/malformed/default summary
behavior are verified, including the two branches unreachable via any current API (`overall_summary` is
never written by any code path today).

**Independent Test**: Seed an interview session with a known question list and assert persistence,
evaluation-stub, and summary-retrieval behavior, independent of the jobs endpoints.

These tasks touch different files than Phases 3–6 and may run **in parallel** with them once Phase 2 is
done.

- [X] T021 [P] [US5] Add `test_submit_answer_session_not_found_returns_404` to
  `backend/tests/contract/test_coach.py`: `POST /api/coach/sessions/99999/answer` with
  `{"question_id": "q1", "answer": "..."}` returns 404 (closes `services/coach.py` line 46, via
  `routers/coach.py`'s `ValueError` → `HTTPException(404)` mapping).
- [X] T022 [P] [US5] Add `test_submit_answer_unknown_question_id_returns_404` to
  `backend/tests/contract/test_coach.py`: create a real prep session via `POST /api/coach/prep`, then
  `POST /api/coach/sessions/{id}/answer` with an unknown `question_id` (e.g. `"does-not-exist"`) returns
  404 (closes `services/coach.py` line 50).
- [X] T023 [P] [US5] Create `backend/tests/services/test_coach.py` (new file, mirroring the direct-service
  pattern in `backend/tests/services/test_oracle.py`) with `test_get_session_summary_data_session_not_found_raises`:
  using the `db_session` fixture, call
  `await get_session_summary_data(db_session, 99999)` directly (no HTTP layer) and assert it raises
  `ValueError` (closes `services/coach.py` line 66).
- [X] T024 [US5] In `backend/tests/services/test_coach.py` (sequential after T023, same file), add:
  - `test_get_session_summary_data_returns_stored_summary_when_valid_json`: seed an `InterviewSession` via
    `db_session` with `overall_summary` set to `json.dumps({"session_id": ..., "overall_score": 0.7,
    "summary": "Good progress", "areas_to_improve": ["pacing"]})`; assert
    `get_session_summary_data` returns that exact parsed dict (closes the `try`/`return result` half of
    lines 71–75).
  - `test_get_session_summary_data_returns_default_when_summary_malformed`: seed an `InterviewSession` with
    `overall_summary` set to the invalid string `"{not valid json"`; assert `get_session_summary_data`
    falls back to the default (`overall_score: 0.0`, `summary: "No answers submitted yet."`,
    `areas_to_improve: []`) instead of raising (closes the `except`/fallback half of lines 71–75; spec.md
    Edge Cases).

**Checkpoint**: Coach's stub evaluation and summary-fallback behavior are locked down at both the API and
service layer, including the two branches with no current API path.

---

## Final Phase: Polish & Verification

- [X] T025 Run `cd backend && make check` (ruff lint + `ruff format --check`, mypy strict, full `pytest` with
  coverage). Confirm zero failures and zero regressions to any previously-passing test (SC-004).
- [X] T026 Run
  `cd backend && uv run pytest --cov=jobforce.routers.jobs --cov=jobforce.services.coach --cov-report=term-missing tests/ -q | grep -E "jobs\.py|coach\.py"`
  and confirm both `jobforce/routers/jobs.py` and `jobforce/services/coach.py` report ≥85% (SC-001, SC-002).
- [X] T027 Run `grep -r "import anthropic" backend/` and confirm zero results (the standing CLAUDE.md
  invariant) — none of the tasks above should touch `coach.py`'s production logic, only its test coverage.
- [X] T028 Confirm (no code change — a documentation/traceability check for the PR description) that
  `POST /api/jobs/bulk-archive` (FR-004) already has full line coverage of its 422-validation and success
  paths from the existing tests in `backend/tests/integration/test_bulk_archive.py`, so no task was needed
  for it — this was verified during the Phase 2 re-baseline (bulk-archive's lines are absent from the T003
  missing-line list).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1. **Blocks every task below** — the missing-line targets in
  Phases 3–7 are only valid once T002/T003 have re-baselined coverage.
- **User Stories (Phases 3–7)**: All depend on Phase 2 completion.
  - Phases 3, 4, 5, 6 (US1–US4) all edit `backend/tests/contract/test_jobs.py` and so **must be applied
    sequentially in that order** (T004→T020), even though the stories themselves are logically independent.
  - Phase 7 (US5) touches different files (`test_coach.py`, new `tests/services/test_coach.py`) and can be
    done **in parallel** with Phases 3–6 by a different contributor, or in any order relative to them.
- **Polish (Final Phase)**: Depends on all of Phases 3–7 being complete.

### Parallel Opportunities

- T021, T022, T023 are marked `[P]` — different files from each other and from every Phase 3–6 task.
- T024 is sequential after T023 (same new file).
- Everything in Phases 3–6 (T004–T020) is sequential — same file, no exceptions.

---

## Implementation Strategy

### MVP First

1. Phase 1 (Setup) → Phase 2 (Foundational config fix + re-baseline) — **do this before anything else**.
2. Phase 3 (User Story 1) — the highest-traffic code path (`GET /api/jobs`) is the MVP slice.
3. **STOP and VALIDATE**: run T003's coverage command again; confirm the lines closed by Phase 3 (141, 179,
   182, 184, 190, 192) no longer appear in the missing list.

### Incremental Delivery

Phase 2 → Phase 3 (US1) → Phase 4 (US2) → Phase 5 (US3) → Phase 6 (US4) → Phase 7 (US5, any time after
Phase 2) → Final Phase. Each user-story phase leaves the suite green and closes a distinct, verifiable set
of lines from the T003 target list — re-run the T003 coverage command after each phase to confirm.

## Notes

- No `[Story]` label conflicts: every task in Phases 3–6 is confirmed non-redundant with existing tests in
  `test_jobs.py` and `test_oracle.py` (see the per-task "distinct from ..." notes above) — do not skip those
  notes when implementing, they explain why a seemingly-duplicate test is actually necessary.
- Commit after each phase checkpoint, not after every single task, since most tasks share one file.
- If any new test in Phases 3–7 exposes an actual behavioral bug (not just a coverage gap), stop and report
  it rather than writing a test that encodes the bug as "expected" — bug fixes are explicitly out of scope
  for this spec (see spec.md Assumptions).
