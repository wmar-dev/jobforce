# Tasks: Oracle and Forge Use Resume as Candidate Profile

**Input**: Design documents from `specs/007-oracle-forge-resume/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

**Note**: Core implementation is already complete in this session. Tasks focus on verification, test coverage (Constitution I), and cleanup.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Verification (No New Infrastructure Needed)

**Purpose**: Confirm the already-implemented changes are correct and the app starts cleanly.

- [x] T001 Verify backend starts without errors: `cd backend && uv run uvicorn jobforce.main:app` in backend/
- [x] T002 [P] Confirm `GET /api/profile` returns 404 (endpoint removed) via curl or httpie
- [x] T003 [P] Confirm `GET /api/resume/base` returns 200 with structured resume data
- [x] T004 [P] Confirm `grep -r "import anthropic" backend/` returns zero results in backend/jobforce/
- [x] T005 [P] Confirm `grep -r "UserProfile" backend/` returns zero results in backend/jobforce/

**Checkpoint**: Backend boots, removed endpoints are gone, no SDK imports remain.

---

## Phase 2: User Story 1 — Oracle ranks jobs using resume (P1) 🎯 MVP

**Goal**: Oracle uses `Resume.structured_data` as the candidate profile in ranking prompts; missing resume yields `confidence: low` + warning.

**Independent Test**: Run `/oracle-rank` with a base resume seeded — rationale in response references specific resume content.

### Tests for User Story 1

> **Write these tests FIRST and confirm they FAIL before skipping to implementation verification**

- [x] T006 [P] [US1] Write unit test for `_build_profile_text(None)` returns "No resume configured." in `backend/tests/services/test_oracle.py`
- [x] T007 [P] [US1] Write unit test for `_build_profile_text(resume)` returns JSON dump of `structured_data` in `backend/tests/services/test_oracle.py`
- [x] T008 [US1] Write integration test: `GET /api/resume/base` → structured_data flows into oracle prompt in `backend/tests/integration/test_oracle_resume.py`

### Implementation verification for User Story 1

- [x] T009 [US1] Run test suite and confirm T006–T008 pass: `cd backend && uv run pytest tests/services/test_oracle.py tests/integration/test_oracle_resume.py -v`
- [x] T010 [US1] Manually run `/oracle-rank` skill against at least one active job and confirm rationale references resume content

**Checkpoint**: Oracle tests pass; `/oracle-rank` produces resume-informed rationales.

---

## Phase 3: User Story 2 — Forge tailors from base resume without resume ID (P2)

**Goal**: `POST /resume/tailor` accepts `{job_id, structured_data}` from the skill; `base_resume_id` is no longer required; missing resume returns 404 with message.

**Independent Test**: Run `/forge-tailor <job_id>` with no resume ID argument — skill completes tailor cycle and posts result successfully.

### Tests for User Story 2

- [x] T011 [P] [US2] Write unit test for `POST /resume/tailor` with valid `{job_id, structured_data}` → 200 with diff in `backend/tests/routers/test_forge.py`
- [x] T012 [P] [US2] Write unit test for `POST /resume/tailor` with no base resume → 404 with helpful message in `backend/tests/routers/test_forge.py`
- [x] T013 [US2] Write unit test for `compute_diff` returns empty list when original equals tailored in `backend/tests/services/test_forge.py`

### Implementation verification for User Story 2

- [x] T014 [US2] Run test suite and confirm T011–T013 pass: `cd backend && uv run pytest tests/routers/test_forge.py tests/services/test_forge.py -v`
- [x] T015 [US2] Manually run `/forge-tailor <job_id>` and confirm it completes without supplying a resume ID

**Checkpoint**: Forge tests pass; `/forge-tailor` works end-to-end without a resume ID argument.

---

## Phase 4: User Story 3 — Resume drives oracle and forge consistently (P3)

**Goal**: Updating the base resume (via `PUT /resume/base`) is immediately reflected in the next oracle and forge run.

**Independent Test**: Update base resume via `PUT /api/resume/base`, then run `/oracle-rank` — rationale references updated content.

### Tests for User Story 3

- [x] T016 [P] [US3] Write integration test: update base resume via `PUT /api/resume/base`, then confirm oracle prompt contains updated content in `backend/tests/integration/test_resume_consistency.py`
- [x] T017 [US3] Write integration test: update base resume, run `POST /resume/tailor`, confirm diff reflects updated base in `backend/tests/integration/test_resume_consistency.py`

### Implementation verification for User Story 3

- [x] T018 [US3] Run test suite and confirm T016–T017 pass: `cd backend && uv run pytest tests/integration/test_resume_consistency.py -v`

**Checkpoint**: All three user stories independently verified.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, spec cleanup, SDK gate enforcement.

- [x] T019 [P] Run full linting gate: `cd backend && uv run ruff check jobforce/` — zero warnings
- [x] T020 [P] Run type-check gate: `cd backend && uv run mypy jobforce/` — zero errors on public API
- [x] T021 [P] Run full test suite: `cd backend && uv run pytest` — 100% pass, no coverage regression
- [x] T022 [P] Run AI SDK gate: `grep -r "import anthropic" backend/jobforce/` — must return zero results
- [x] T023 Update `backend/jobforce/db/seed.py` docstring if needed to reflect `_seed_base_resume` addition in `backend/jobforce/db/seed.py`
- [x] T024 Update spec status from "Draft" to "Implemented" in `specs/007-oracle-forge-resume/spec.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Verification)**: No dependencies — start immediately
- **Phase 2 (US1)**: Depends on Phase 1 checkpoint passing
- **Phase 3 (US2)**: Can start in parallel with Phase 2 — independent files
- **Phase 4 (US3)**: Depends on Phase 2 and Phase 3 checkpoints
- **Phase 5 (Polish)**: Depends on all prior phases complete

### User Story Dependencies

- **US1 (Oracle)**: Independent — `backend/jobforce/services/oracle.py`, skill `oracle-rank/SKILL.md`
- **US2 (Forge)**: Independent — `backend/jobforce/routers/forge.py`, `backend/jobforce/services/forge.py`, skill `forge-tailor/SKILL.md`
- **US3 (Consistency)**: Depends on US1 + US2 both working (integration test over both)

### Parallel Opportunities

```bash
# Phase 1: all verification tasks run in parallel
T002, T003, T004, T005

# Phase 2 + Phase 3: test writing is parallel across stories
T006, T007   # oracle unit tests (parallel with each other)
T011, T012   # forge router tests (parallel with each other)
T013         # forge service test

# Phase 5: all quality gates in parallel
T019, T020, T021, T022
```

---

## Implementation Strategy

### MVP First (User Story 1 — Oracle)

1. Complete Phase 1: Verification
2. Complete Phase 2: Oracle tests + manual smoke test
3. **STOP and VALIDATE**: `/oracle-rank` produces resume-driven rationales
4. Proceed to Phase 3 (Forge) once Oracle is confirmed

### Incremental Delivery

1. Phase 1: Confirm existing implementation is correct
2. Phase 2: Add oracle tests → green → Oracle MVP complete
3. Phase 3: Add forge tests → green → Forge complete
4. Phase 4: Add consistency tests → green → Full feature complete
5. Phase 5: Polish + gates → merge-ready

---

## Notes

- [P] tasks = different files, no unresolved dependencies — safe to run concurrently
- Constitution I (Test-First) applies to any net-new logic; existing code gets tests added retroactively here
- Constitution VI (no SDK): enforced by T004 and T022 (grep gate)
- All tests live under `backend/tests/` mirroring source paths 1:1 per Constitution I
- Commit after each phase checkpoint
