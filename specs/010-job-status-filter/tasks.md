---

description: "Task list for Job Status Filtering & Triage (feature 010)"
---

# Tasks: Job Status Filtering & Triage

**Input**: Design documents from `specs/010-job-status-filter/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Organization**: Tasks grouped by user story; tests included (Constitution Principle I — Test-First is NON-NEGOTIABLE).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Migration and shared type changes that all stories depend on.

- [x] T001 Create DB migration file `backend/jobforce/db/migrations/010_add_triage_statuses.sql` per data-model.md (table-recreate pattern for SQLite CHECK constraint)
- [x] T002 Run migration against local DB: `sqlite3 backend/data/jobforce.db < backend/jobforce/db/migrations/010_add_triage_statuses.sql`
- [x] T003 Update `_VALID_STATUSES` constant in `backend/jobforce/db/models.py` to include `'archived'` and `'shortlisted'`
- [x] T004 Update `_VALID_TRANSITIONS` dict in `backend/jobforce/services/scout.py` per data-model.md transition graph
- [x] T005 [P] Update `PipelineStatus` union type in `frontend/src/lib/types.ts` to add `"archived"` and `"shortlisted"`
- [x] T006 [P] Add `archived` and `shortlisted` entries to `STATUS_CONFIG` in `frontend/src/components/jobs/StatusBadge.tsx`

**Checkpoint**: Migration applied; backend constants updated; frontend types compile cleanly (`npm run lint` passes).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend default-exclusion behaviour — must be in place before any frontend story work.

**⚠️ CRITICAL**: US1 and US2 frontend work depends on this phase being complete.

- [x] T007 Write failing unit test for default exclusion in `backend/tests/unit/test_triage_statuses.py`: assert `GET /api/jobs` with no status filter excludes archived jobs
- [x] T008 Update `GET /api/jobs` in `backend/jobforce/routers/jobs.py` to add `WHERE status != 'archived'` when no `status` query param is provided (make T007 pass)
- [x] T009 Write failing unit test in `backend/tests/unit/test_triage_statuses.py`: assert `GET /api/jobs?status=archived` returns only archived jobs
- [x] T010 Verify T009 passes with existing filter logic (no code change expected — existing `status` param already handles this)
- [x] T011 Run `cd backend && make check` — all gates must pass before proceeding

**Checkpoint**: Default job list excludes archived. `make check` green.

---

## Phase 3: User Story 1 — Archive Low-Score Jobs (Priority: P1) 🎯 MVP

**Goal**: User can archive a job from the job list with one action; archived jobs are hidden from the default view but preserved and retrievable.

**Independent Test**: Mark a job as archived via `PATCH /api/jobs/{id}/status` → confirm it disappears from default `GET /api/jobs` → confirm it appears in `GET /api/jobs?status=archived`.

### Tests for User Story 1

> **Write these tests FIRST — confirm they FAIL before implementing T018/T019.**

- [x] T012 [P] [US1] Write failing unit tests for updated `_VALID_TRANSITIONS` in `backend/tests/unit/test_triage_statuses.py`: assert `saved → archived` allowed; `archived → saved` allowed; `shortlisted → archived` allowed
- [x] T013 [P] [US1] Write failing integration test `backend/tests/integration/test_bulk_archive.py`: `PATCH /api/jobs/{id}/status` with `{"status": "archived"}` from `saved` returns 200 with new status and records a `status_transitions` row

### Implementation for User Story 1

- [x] T014 [US1] Verify `_VALID_TRANSITIONS` update from T004 makes T012 pass; adjust if needed
- [x] T015 [US1] Verify `PATCH /api/jobs/{id}/status` already handles `archived` via existing `transition_status()` service — make T013 pass (no new endpoint code needed if transition graph is correct)
- [x] T016 [P] [US1] Add "Archive" inline action button to each job row in `frontend/src/components/jobs/JobTable.tsx` — calls `patchJobStatus(id, "archived")` then triggers SWR revalidate
- [x] T017 [P] [US1] Add "Active" tab (rename from "All") and "Archived" tab to `STATUS_TABS` in `frontend/src/app/jobs/page.tsx`; add `"archived"` and `"shortlisted"` to `VALID_STATUSES` set
- [x] T018 [US1] Wire the jobs page "Active" tab default to pass no status filter (relies on backend default exclusion from Phase 2)
- [x] T019 [US1] Run `cd backend && make check` and `cd frontend && npm run lint && npm test` — all must pass

**Checkpoint**: Archive button visible on job cards. Archiving a job removes it from Active view. Archived tab shows archived jobs. `make check` green.

---

## Phase 4: User Story 2 — Mark Jobs to Apply To (Priority: P2)

**Goal**: User can shortlist a job with one inline action; shortlisted jobs are visually distinct and filterable; shortlisting an archived job restores it to active.

**Independent Test**: Shortlist a job → confirm it shows `shortlisted` status badge in the list → filter by "Shortlisted" tab → confirm only shortlisted jobs appear.

### Tests for User Story 2

> **Write these tests FIRST — confirm they FAIL before implementing T024/T025.**

- [x] T020 [P] [US2] Write failing unit tests in `backend/tests/unit/test_triage_statuses.py`: assert `saved → shortlisted` allowed; `archived → shortlisted` allowed; `shortlisted → saved` allowed; `shortlisted → applied` allowed
- [x] T021 [P] [US2] Write failing integration test in `backend/tests/integration/test_bulk_archive.py`: `PATCH /api/jobs/{id}/status` with `{"status": "shortlisted"}` from `archived` returns 200 and job is no longer in archived list

### Implementation for User Story 2

- [x] T022 [US2] Verify T020/T021 pass with transition graph from T004; adjust `_VALID_TRANSITIONS` if needed
- [x] T023 [P] [US2] Add "Shortlist" inline action button to each job row in `frontend/src/components/jobs/JobTable.tsx` — calls `patchJobStatus(id, "shortlisted")` then triggers SWR revalidate; show "Unshortlist" (→ saved) when job is already shortlisted
- [x] T024 [P] [US2] Add "Shortlisted" tab to `STATUS_TABS` in `frontend/src/app/jobs/page.tsx` (tab added in T017; verify grouping by company is visible in the filtered list)
- [x] T025 [US2] Add `shortlisted` fetch to `frontend/src/app/coach/page.tsx` alongside existing `applied` and `interviewing` fetches so shortlisted jobs appear in the Coach job selector
- [x] T026 [US2] Run `cd backend && make check` and `cd frontend && npm run lint && npm test` — all must pass

**Checkpoint**: Shortlist button on job cards. Shortlisting an archived job moves it back to active. "Shortlisted" filter tab works. Shortlisted jobs appear on Coach page.

---

## Phase 5: User Story 3 — Bulk Archive by Score Threshold (Priority: P3)

**Goal**: User can archive all `saved` jobs with fit_score < 50 in one action from the jobs page; shortlisted jobs are never touched.

**Independent Test**: Trigger `POST /api/jobs/bulk-archive` → confirm all `saved` jobs with `fit_score < 0.50` are now archived → confirm shortlisted jobs are untouched → confirm unscored jobs are untouched.

### Tests for User Story 3

> **Write these tests FIRST — confirm they FAIL before implementing T030/T031.**

- [x] T027 [P] [US3] Write failing integration test in `backend/tests/integration/test_bulk_archive.py`: `POST /api/jobs/bulk-archive` archives only `saved` jobs with `fit_score < 0.50`; returns `{"archived_count": N}`
- [x] T028 [P] [US3] Write failing integration test: bulk archive does NOT archive shortlisted jobs, unscored jobs, or pipeline-stage jobs (`applied`, `interviewing`, etc.)

### Implementation for User Story 3

- [x] T029 [US3] Implement `bulk_archive_low_score(session)` service function in `backend/jobforce/services/scout.py` — single transaction, selects `saved` jobs with `fit_score IS NOT NULL AND fit_score < 0.50`, updates status to `archived`, inserts `status_transitions` rows, returns count
- [x] T030 [US3] Add `POST /api/jobs/bulk-archive` endpoint to `backend/jobforce/routers/jobs.py` — calls `bulk_archive_low_score()`, returns `{"archived_count": N}` — make T027/T028 pass
- [x] T031 [P] [US3] Add `bulkArchive()` fetch wrapper to `frontend/src/lib/api.ts`: `POST /api/jobs/bulk-archive` → returns `{ archived_count: number }`
- [x] T032 [US3] Add "Bulk Archive Low Scores" button to the jobs page toolbar in `frontend/src/app/jobs/page.tsx` — calls `bulkArchive()`, shows result count in a toast/inline message, triggers SWR revalidate
- [x] T033 [US3] Run `cd backend && make check` and `cd frontend && npm run lint && npm test` — all must pass

**Checkpoint**: Bulk archive button on jobs page. Triggering it archives all qualifying saved jobs and shows count. Shortlisted and unscored jobs unaffected.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T034 [P] Verify `PATCH /api/jobs/{id}/status` for `archived` and `shortlisted` transitions is covered in existing `backend/tests/` — add any missing edge-case unit tests to `backend/tests/unit/test_triage_statuses.py`
- [x] T035 [P] Verify `frontend/src/components/jobs/StatusBadge.tsx` renders correctly for `archived` (muted) and `shortlisted` (amber) in the job list
- [ ] T036 Run full `quickstart.md` smoke test sequence against local dev environment
- [x] T037 Run `cd backend && make check` final gate — zero warnings, zero type errors, coverage not regressed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (T003, T004 must be done before T007–T010)
- **Phase 3 (US1)**: Depends on Phase 2 completion
- **Phase 4 (US2)**: Depends on Phase 2 completion; integrates with US1 transition graph
- **Phase 5 (US3)**: Depends on Phase 2 completion; independent of US1/US2 UI
- **Phase 6 (Polish)**: Depends on all desired user stories complete

### User Story Dependencies

- **US1 (P1)**: Can start after Phase 2 — no dependency on US2 or US3
- **US2 (P2)**: Can start after Phase 2 — shares transition graph with US1; verify T022 after T014
- **US3 (P3)**: Can start after Phase 2 — backend service is independent; frontend button is independent of US1/US2 buttons

### Within Each Story

- Tests MUST be written first and confirmed failing before implementation
- Backend model/service changes before endpoint changes
- Backend complete before frontend integration

### Parallel Opportunities

- T005 and T006 (frontend type changes) can run in parallel with T003/T004 (backend constants)
- T012 and T013 (US1 tests) can be written in parallel
- T016 and T017 (US1 frontend) can be implemented in parallel
- T020 and T021 (US2 tests) can be written in parallel
- T023 and T024 (US2 frontend) can be implemented in parallel
- T027 and T028 (US3 tests) can be written in parallel
- T031 (US3 frontend api wrapper) can be written in parallel with T029/T030 (US3 backend)

---

## Parallel Example: User Story 1

```bash
# Write tests in parallel first (both MUST fail):
Task T012: "Unit tests for saved→archived, archived→saved transitions in backend/tests/unit/test_triage_statuses.py"
Task T013: "Integration test for PATCH /api/jobs/{id}/status archived in backend/tests/integration/test_bulk_archive.py"

# Then implement backend (T014, T015) before frontend:
Task T016: "Archive inline button in frontend/src/components/jobs/JobTable.tsx"
Task T017: "Active/Archived tabs in frontend/src/app/jobs/page.tsx"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (migration + constants + types)
2. Complete Phase 2: Foundational (default exclusion)
3. Complete Phase 3: User Story 1 (archive flow end-to-end)
4. **STOP and VALIDATE**: Archive a job → disappears from Active → appears in Archived tab
5. Ship if sufficient — US2 and US3 can follow independently

### Incremental Delivery

1. Phase 1 + Phase 2 → Foundation (migration applied, default exclusion active)
2. Phase 3 → Archive flow working end-to-end (MVP)
3. Phase 4 → Shortlist flow + Coach page integration
4. Phase 5 → Bulk archive button
5. Phase 6 → Polish and final gate check

---

## Notes

- **[P]** tasks touch different files and have no dependency on incomplete sibling tasks
- **[Story]** label maps each task to a user story for traceability
- Constitution Principle I: Tests MUST be written and confirmed failing before implementation
- Constitution Principle VI: No Anthropic SDK usage — this feature has none
- `fit_score` is stored as 0.0–1.0 float; threshold of 50 (user-facing) = `< 0.50` in queries
- The "All" tab rename to "Active" is a UX clarification, not a breaking API change
