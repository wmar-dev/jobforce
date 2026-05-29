# Tasks: Recruiter Notes

**Input**: Design documents from `specs/008-recruiter-notes/`

**Prerequisites**: plan.md ✅, spec.md ✅

**Organization**: Tasks grouped by user story (P1 → P2 → P3). Constitution Principle I enforced — contract tests written and confirmed failing before each implementation block.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: DB migration and plan alignment — required before any story work.

- [x] T001 Update plan.md to reflect single-note upsert model (PATCH endpoint replaces POST/DELETE) in `specs/008-recruiter-notes/plan.md`
- [x] T002 Add `updated_at` column to `meeting_notes` table via Alembic migration in `backend/jobforce/db/` (or inline `ALTER TABLE` in `backend/jobforce/db/init.py`)
- [x] T003 Add `updated_at` field to `MeetingNote` SQLAlchemy model in `backend/jobforce/db/models.py`

**Checkpoint**: DB schema ready; `MeetingNote` model has `created_at` + `updated_at`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend Pydantic schemas and API plumbing shared across all stories.

- [x] T004 Add `JobNoteOut` and `JobNoteUpsert` Pydantic models to `backend/jobforce/routers/jobs.py`
- [x] T005 [P] Add `JobNote` TypeScript type to `frontend/src/lib/types.ts`
- [x] T006 [P] Add `getJobNote`, `upsertJobNote` API functions to `frontend/src/lib/api.ts`
- [x] T007 Add `useJobNote` SWR hook in `frontend/src/hooks/useJobNote.ts`

**Checkpoint**: Schemas defined; frontend API layer and hook ready.

---

## Phase 3: User Story 1 — Add Notes to a Job (Priority: P1) 🎯 MVP

**Goal**: User can open a job, type a note, save it, and see it on return.

**Independent Test**: Open any job listing → type a note → navigate away → return to job → note is visible.

### Tests for User Story 1

> **Constitution Principle I: Write tests FIRST — confirm they FAIL before implementing.**

- [x] T008 [US1] Write contract tests for `GET /api/jobs/{id}/note` and `PUT /api/jobs/{id}/note` in `backend/tests/contract/test_jobs.py` — confirm tests fail (no endpoints yet)

### Implementation for User Story 1

- [x] T009 [US1] Implement `GET /api/jobs/{job_id}/note` endpoint in `backend/jobforce/routers/jobs.py` — returns the single `JobNoteOut` or 404
- [x] T010 [US1] Implement `PUT /api/jobs/{job_id}/note` endpoint in `backend/jobforce/routers/jobs.py` — upserts the note body, sets `updated_at`; returns `JobNoteOut`
- [x] T011 [US1] Add Notes section to job detail page in `frontend/src/app/jobs/[id]/page.tsx` — textarea pre-populated from `useJobNote`, save button triggers `upsertJobNote`, shows `updated_at` as "last edited"
- [x] T012 [US1] Run contract tests — confirm they now pass

**Checkpoint**: User Story 1 fully functional. Notes persist across refresh.

---

## Phase 4: User Story 2 — Notes Indicator in Job List (Priority: P2)

**Goal**: Jobs with a note show a visible indicator in the job list.

**Independent Test**: Add a note to one job → return to `/jobs` → that job row shows a note indicator; jobs without notes show none.

### Tests for User Story 2

> **Constitution Principle I: Write tests FIRST — confirm they FAIL.**

- [x] T013 [US2] Extend `GET /api/jobs` contract test to assert `has_note` boolean field is present on each item in `backend/tests/contract/test_jobs.py` — confirm test fails

### Implementation for User Story 2

- [x] T014 [US2] Add `has_note: bool` field to `JobListingOut` Pydantic model in `backend/jobforce/routers/jobs.py`
- [x] T015 [US2] Update `GET /api/jobs` query to LEFT JOIN `meeting_notes` and populate `has_note` in `backend/jobforce/routers/jobs.py`
- [x] T016 [US2] Add `has_note` to `JobListing` TypeScript type in `frontend/src/lib/types.ts`
- [x] T017 [US2] Add note indicator (pencil/note icon from `lucide-react`) to `JobTable.tsx` rows where `has_note` is true in `frontend/src/components/jobs/JobTable.tsx`
- [x] T018 [US2] Run contract tests — confirm they now pass

**Checkpoint**: Job list shows note indicators. User Stories 1 and 2 both independently functional.

---

## Phase 5: User Story 3 — Edit and Clear Notes (Priority: P3)

**Goal**: User can update an existing note or clear it entirely; clearing removes the indicator.

**Independent Test**: Edit an existing note → save → verify updated content persists. Clear the note → verify indicator disappears in job list.

### Tests for User Story 3

> **Constitution Principle I: Write tests FIRST — confirm they FAIL.**

- [x] T019 [US3] Write contract tests for `DELETE /api/jobs/{id}/note` in `backend/tests/contract/test_jobs.py` — confirm test fails

### Implementation for User Story 3

- [x] T020 [US3] Implement `DELETE /api/jobs/{job_id}/note` endpoint in `backend/jobforce/routers/jobs.py` — removes the note row; subsequent GET returns 404
- [x] T021 [US3] Add `deleteJobNote` function to `frontend/src/lib/api.ts`
- [x] T022 [US3] Add clear/delete button to Notes section in `frontend/src/app/jobs/[id]/page.tsx` — calls `deleteJobNote`, clears textarea, triggers SWR revalidation
- [x] T023 [US3] Run contract tests — confirm they now pass

**Checkpoint**: Full note lifecycle (create → edit → delete) works. All 3 user stories independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T024 [P] Run `make check` in `backend/` — ruff lint zero warnings, mypy zero errors, all tests pass
- [x] T025 [P] Verify `grep -r "import anthropic" backend/` returns zero results (Constitution VI gate) — pre-existing in coach.py only, not introduced by this feature
- [ ] T026 Smoke-test the full flow in the running app: add note → see indicator → edit note → clear note → indicator gone
- [x] T027 [P] Update `specs/008-recruiter-notes/plan.md` contracts section to document the three job-note endpoints

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (T002/T003 DB migration complete)
- **Phase 3 (US1)**: Depends on Phase 2 — BLOCKS US2 and US3
- **Phase 4 (US2)**: Depends on Phase 3 (needs `has_note` derived from note existence)
- **Phase 5 (US3)**: Depends on Phase 3 (note must exist to clear it)
- **Phase 6 (Polish)**: Depends on all desired stories complete

### Within Each Story

1. Write tests → confirm FAIL
2. Backend model/schema → endpoint
3. Frontend type → API function → hook → UI component
4. Run tests → confirm PASS

### Parallel Opportunities

- T005, T006 (frontend types + API) can run in parallel with T004 (backend schemas)
- T008 test writing can start as soon as T004 schemas exist
- T013 (US2 test), T019 (US3 test) can be written in parallel once US1 is complete
- T024, T025, T027 (polish) can run in parallel

---

## Parallel Example: Phase 2 Foundational

```
Parallel batch:
  T005 — frontend/src/lib/types.ts  (JobNote type)
  T006 — frontend/src/lib/api.ts    (getJobNote, upsertJobNote)
  T004 — backend routers/jobs.py    (Pydantic schemas)

Sequential after:
  T007 — frontend/src/hooks/useJobNote.ts  (depends on T006)
```

---

## Implementation Strategy

### MVP (User Story 1 only — Phases 1–3)

1. Complete Phase 1: DB migration + model update
2. Complete Phase 2: Schemas and API plumbing
3. Complete Phase 3: US1 — notes on job detail page
4. **STOP and VALIDATE**: open a job, add a note, refresh, confirm persistence
5. Ship MVP if sufficient

### Incremental Delivery

1. Phases 1–3 → US1 (core notes) → validate
2. Phase 4 → US2 (list indicator) → validate
3. Phase 5 → US3 (clear notes) → validate
4. Phase 6 → polish + quality gates

---

## Notes

- [P] = different files, no shared state, safe to run in parallel
- `make check` must pass before any PR (ruff, mypy, pytest — Constitution II)
- `updated_at` migration: if SQLite `ALTER TABLE` approach is used (no Alembic), ensure it is idempotent (wrap in `IF NOT EXISTS` or equivalent)
- The existing company-notes append model is NOT changed by this feature — job notes use upsert, company notes stay as-is
