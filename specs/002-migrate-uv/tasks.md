# Tasks: Migrate Dependency Management to uv

**Input**: Design documents from `specs/002-migrate-uv/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Organization**: Tasks are grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US4)

---

## Phase 1: Setup

**Purpose**: Generate the lockfile — required before any Makefile or doc changes can be validated.

- [x] T001 Run `cd backend && uv lock` to generate backend/uv.lock from pyproject.toml

**Checkpoint**: `backend/uv.lock` exists and is committed.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: No foundational blockers beyond T001 — all user story tasks depend only on the lockfile existing.

_(No tasks — setup is minimal for this tooling migration)_

---

## Phase 3: User Story 1 — Developer Installs for the First Time (Priority: P1) 🎯 MVP

**Goal**: `uv sync --extra dev` in `backend/` creates the venv and installs all deps from the lockfile.

**Independent Test**: On a clean checkout with no `backend/.venv/`, run `uv sync --extra dev` — venv is created, all deps install, app starts with `uvicorn jobforce.main:app`.

### Implementation for User Story 1

- [x] T002 [US1] Add `sync` target (`uv sync --extra dev`) to backend/Makefile
- [x] T003 [US1] Run `cd backend && uv sync --extra dev` to verify lockfile installs correctly and `.venv/` is created

**Checkpoint**: `make sync` from `backend/` creates `backend/.venv/` and installs all packages.

---

## Phase 4: User Story 2 — Developer Runs Quality Gates (Priority: P1)

**Goal**: `make check` continues to pass using the uv-managed environment.

**Independent Test**: Run `make check` from `backend/` with only the uv-synced venv — all lint, typecheck, and test gates pass.

### Implementation for User Story 2

- [x] T004 [US2] Verify `make check` passes in backend/ after `uv sync --extra dev` (ruff, mypy, pytest all use `.venv/bin/` paths already set in Makefile)

**Checkpoint**: `make check` exits 0 — 65 tests pass, 1 skipped, ruff clean, mypy clean.

---

## Phase 5: User Story 3 — Developer Adds or Updates a Dependency (Priority: P2)

**Goal**: Workflow for adding a new package is documented; `uv lock` + `uv sync` keeps envs in sync.

**Independent Test**: The spec documents the add-package workflow clearly enough that a developer can follow it without asking.

### Implementation for User Story 3

- [x] T005 [US3] Update root Makefile `install` target: replace `pip install -e ".[dev]"` with `cd backend && uv sync --extra dev` in Makefile (root)

**Checkpoint**: `make install` from project root calls `uv sync --extra dev` instead of pip.

---

## Phase 6: User Story 4 — quickstart.md Reflects uv Workflow (Priority: P2)

**Goal**: All developer-facing docs reference `uv` exclusively; zero `pip install -e` references remain.

**Independent Test**: Grep confirms no `pip install -e` in README.md, docs/quickstart.md, or specs/001-job-force-app/quickstart.md.

### Implementation for User Story 4

- [x] T006 [P] [US4] Update README.md Prerequisites section: add `uv` bullet, remove pip/venv mention; update Setup section: replace `pip install -e ".[dev]"` with `uv sync --extra dev`
- [x] T007 [P] [US4] Update specs/001-job-force-app/quickstart.md install step to use `uv sync --extra dev` instead of `pip install -e ".[dev]"`
- [x] T008 [US4] Run `grep -r "pip install" README.md docs/ specs/001-job-force-app/quickstart.md` to confirm zero remaining pip references

**Checkpoint**: All setup docs reference uv exclusively.

---

## Phase 7: Polish & Verification

**Purpose**: End-to-end validation and final cleanup.

- [x] T009 Run `make check` from backend/ one final time to confirm zero regressions after all Makefile and doc changes
- [x] T010 [P] Add `backend/uv.lock` and all modified files to git staging; confirm `.venv/` is gitignored

**Checkpoint**: All gates pass, lockfile committed, migration complete.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start here
- **Phase 3 (US1)**: Depends on T001 (uv.lock must exist before sync can be verified)
- **Phase 4 (US2)**: Depends on T002–T003 (venv must exist for make check to run)
- **Phase 5 (US3)**: Independent of US1/US2 — root Makefile edit, no env required
- **Phase 6 (US4)**: Independent — doc edits only, T006 and T007 can run in parallel
- **Phase 7 (Polish)**: Depends on all prior phases complete

### Parallel Opportunities

- T006 and T007 (doc updates) can run simultaneously
- T005 (root Makefile) can run in parallel with T002–T004

---

## Parallel Example: User Story 4

```bash
# Both doc updates can run simultaneously:
Task: "Update README.md Prerequisites and Setup sections"
Task: "Update specs/001-job-force-app/quickstart.md install step"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1 (T001): Generate lockfile
2. Complete Phase 3 (T002–T003): Verify `uv sync` works
3. Complete Phase 4 (T004): Verify `make check` passes
4. **STOP and VALIDATE**: Foundation of uv migration confirmed working

### Full Migration

1. Complete MVP (above)
2. Phase 5 (T005): Update root Makefile
3. Phase 6 (T006–T008): Update all docs
4. Phase 7 (T009–T010): Final validation + commit

---

## Notes

- No source code changes — all tasks are config, tooling, and docs
- `make check` is the single regression gate; it must pass after every phase
- The lockfile (`uv.lock`) must be committed alongside pyproject.toml
- `.venv/` stays at `backend/.venv/` — uv default when run from `backend/`
- `uv sync --extra dev` is required (not bare `uv sync`) to include dev dependencies
