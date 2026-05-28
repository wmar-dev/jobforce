---
description: "Task list for Oracle SDK-Free Job Ranking"
---

# Tasks: Oracle SDK-Free Job Ranking

**Input**: Design documents from `specs/005-oracle-no-sdk/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Constitution requires tests for non-trivial logic. The new score-write
fields in `PATCH /jobs/{id}` and the 501 stub on `POST /oracle/rank` require
contract tests before implementation.

**Organization**: Tasks grouped by user story; US2 (remove SDK) is foundational
and must complete before US1 (skill) is validated end-to-end.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Maps to user story (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Confirm baseline and identify all SDK references to remove.

- [x] T001 Audit all `anthropic` references in the backend: run `grep -rn "anthropic" backend/jobforce/` and record every file and line that must change
- [x] T002 Confirm `PATCH /api/jobs/{id}` exists and works: run `curl -s -X PATCH http://localhost:8000/api/jobs/2 -H "Content-Type: application/json" -d '{"title":"test"}' | python3 -m json.tool`

---

## Phase 2: Foundational — Remove SDK from Backend (US2 prerequisite)

**Purpose**: Eliminate the Anthropic SDK from the backend entirely. This unblocks
all user stories and resolves the constitution violation.

**⚠️ CRITICAL**: FR-001 (zero SDK imports) must be satisfied before any other
story can be declared complete. Run tests after each task.

- [x] T003 Write contract test for `POST /api/oracle/rank` returning 501 in `backend/tests/contract/test_oracle.py` — add after existing tests, assert `resp.status_code == 501` and response body contains "Claude Code"
- [x] T004 Rewrite `backend/jobforce/services/oracle.py`: delete `rank_jobs()` and the `anthropic` import; keep `_build_profile_text`, `_confidence_label`, `_build_ranking_prompt`, `_parse_ranking_response` as pure helper functions; add module docstring noting AI is now performed by Claude Code
- [x] T005 Rewrite `backend/jobforce/routers/oracle.py` `post_rank` endpoint: remove `rank_jobs` call; return `JSONResponse(status_code=501, content={"detail": "Oracle ranking is now performed via Claude Code. Run /oracle-rank in Claude Code to score jobs."})`
- [x] T006 Remove `"anthropic>=0.28"` from `[project].dependencies` in `backend/pyproject.toml`
- [x] T007 [P] Extend `JobPatchRequest` in `backend/jobforce/routers/jobs.py` to accept `fit_score: float | None`, `fit_scored: int | None`, `fit_confidence: str | None`, `fit_rationale: str | None` — update `setattr` loop to write these fields
- [x] T008 [P] Write contract test for score-write via `PATCH /api/jobs/{id}` in `backend/tests/contract/test_oracle.py`: ingest a job, PATCH with `fit_score=0.85`, `fit_scored=1`, `fit_confidence="high"`, `fit_rationale="Great fit"`, then GET and assert all fields persisted correctly
- [x] T009 Verify SDK removed: run `grep -r "anthropic" backend/jobforce/` — must return no output; run `cd backend && make test` — all tests must pass

**Checkpoint**: `grep -r "anthropic" backend/jobforce/` returns nothing. `make test` passes. Score-write via `PATCH /api/jobs/{id}` works.

---

## Phase 3: User Story 1 — Rank Jobs via Claude Code Skill (Priority: P1) 🎯 MVP

**Goal**: The `/oracle-rank` skill fetches jobs and profile, scores each job using
Claude Code's reasoning, and writes results back to the backend.

**Independent Test**: Run `/oracle-rank` in Claude Code with at least one job that
has a description. Verify scores appear in `GET /api/jobs/{id}` (`fit_scored=true`,
`fit_score` non-null) without any SDK call in the backend.

### Implementation for User Story 1

- [x] T010 [US1] Rewrite `.claude/skills/oracle-rank.md`: replace the existing skill with a new version that (1) fetches active jobs from `GET /api/jobs`, (2) fetches profile from `GET /api/profile`, (3) reasons about fit for each job inline, (4) writes each result via `PATCH /api/jobs/{id}` with fit_score (0.0–1.0), fit_scored=1, fit_confidence, fit_rationale, (5) prints a ranked summary
- [x] T011 [US1] Add input parsing to `.claude/skills/oracle-rank.md`: if job IDs are provided as arguments, fetch only those jobs via `GET /api/jobs?limit=200` and filter; if no arguments, rank all jobs with status in (saved, applied, interviewing)
- [x] T012 [P] [US1] Add sparse-description handling to `.claude/skills/oracle-rank.md`: if a job description is fewer than 100 characters, score it with confidence="low" and append warning "Job description is too sparse for reliable scoring" to the output
- [x] T013 [P] [US1] Add score clamping to `.claude/skills/oracle-rank.md`: ensure all scores are clamped to 0.0–1.0 before writing; note any out-of-range values in the completion output
- [x] T014 [US1] Add error handling to `.claude/skills/oracle-rank.md`: if backend is unreachable on any fetch, print a clear error and exit without partial writes; if a single job PATCH fails, log the failure and continue to the next job

**Checkpoint**: Run `/oracle-rank` → scores appear on `/oracle` page and in `GET /api/jobs/{id}`. Backend logs show no SDK calls.

---

## Phase 4: User Story 2 — Remove SDK Dependency (Priority: P2)

**Note**: The core SDK removal work is in Phase 2 (Foundational). This phase
validates and confirms the removal is complete end-to-end.

### Implementation for User Story 2

- [x] T015 [US2] Run `grep -r "anthropic" backend/` (including `pyproject.toml`) and confirm zero matches; document result as a comment in the PR description
- [x] T016 [US2] Reinstall backend dependencies without anthropic: run `cd backend && uv sync` and confirm no `anthropic` package in the installed environment
- [x] T017 [P] [US2] Run the full backend test suite: `cd backend && make test` — all tests must pass; record pass count

**Checkpoint**: Zero SDK references in any backend file. `make test` passes. `uv sync` installs no `anthropic` package.

---

## Phase 5: User Story 3 — Oracle UI Reflects New Workflow (Priority: P3)

**Goal**: The Oracle frontend page no longer shows a "Run Oracle Ranking" button.
Instead it shows an instruction to use `/oracle-rank` in Claude Code.

**Independent Test**: Open `http://localhost:3000/oracle` — the page must not
contain a button that POSTs to `/api/oracle/rank`. It must contain an instruction
mentioning Claude Code and `/oracle-rank`.

### Implementation for User Story 3

- [x] T018 [US3] Update `frontend/src/app/oracle/page.tsx`: remove the `runRanking` function, remove the `isLoading` and `error` state, replace the `<button onClick={runRanking}>` section with a static instruction panel: `Run /oracle-rank in Claude Code to score your jobs against your profile.`
- [x] T019 [P] [US3] Remove the `rankJobs` API call from `frontend/src/lib/api.ts` (or equivalent) if it exists only for the Oracle page button — check with `grep -n "rankJobs" frontend/src/` before deleting
- [x] T020 [US3] Keep the results display section in `frontend/src/app/oracle/page.tsx` — remove the `results` state that was populated by the button; the Oracle page should instead display previously-ranked jobs fetched from `GET /api/jobs?fit_scored=true` (or similar) so scores written by the skill are visible without re-running

**Checkpoint**: `http://localhost:3000/oracle` shows no "Run Oracle Ranking" button. Previously ranked jobs (from the skill) are visible on the page.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T021 [P] Run full end-to-end validation per `specs/005-oracle-no-sdk/quickstart.md`: backend running, profile set, run `/oracle-rank`, verify scores in UI, verify `grep anthropic` empty
- [x] T022 [P] Update `backend/jobforce/services/oracle.py` module docstring to reflect the new architecture: "AI ranking is performed by Claude Code via the /oracle-rank skill; this module retains helper functions for prompt formatting reference"
- [x] T023 Remove `.playwright-mcp/` from `.gitignore` exclusion or confirm it's already ignored: run `git status` and ensure Playwright snapshot files are not staged

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — audit first
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational (needs score-write endpoint working)
- **US2 (Phase 4)**: Depends on Foundational (validates removal is complete)
- **US3 (Phase 5)**: Independent of US1/US2 — can run in parallel with Phase 3+
- **Polish (Phase 6)**: Depends on all story phases complete

### Within Each Phase

- T003 (test for 501) MUST be written before T005 (implement 501 stub)
- T008 (test for score-write) MUST be written before T007 (implement score fields) — or simultaneously since they touch different files [P]
- T010–T011 must be sequential (T011 extends T010's skill file)
- T012–T013 can run in parallel with each other after T010

### Parallel Opportunities

```bash
# Phase 2 — after T004/T005 are done:
T007  # extend JobPatchRequest  (jobs.py)
T008  # write score-write test  (test_oracle.py)

# Phase 3 — after T011 is done:
T012  # sparse description handling  (oracle-rank.md section)
T013  # score clamping               (oracle-rank.md section)

# Phase 4:
T015  # grep audit
T016  # uv sync
T017  # make test

# Phase 5 — after T018:
T019  # remove rankJobs from api.ts

# Phase 6:
T021  # end-to-end validation
T022  # docstring update
```

---

## Implementation Strategy

### MVP First (US2 + US1)

1. Phase 1: Audit (T001–T002)
2. Phase 2: Remove SDK + add score-write (T003–T009)
3. Phase 3: Rewrite oracle-rank skill (T010–T014)
4. **STOP and VALIDATE**: Run `/oracle-rank`, check scores appear, check `grep anthropic` clean
5. Ship: constitution violation resolved, skill works

### Full Delivery

1. MVP above
2. Phase 4: Confirm removal end-to-end (T015–T017)
3. Phase 5: Fix Oracle UI (T018–T020)
4. Phase 6: Polish (T021–T023)

---

## Notes

- T003 and T008 are test-first tasks — they MUST be written before their corresponding implementation tasks (constitution Principle I)
- The `oracle-rank.md` skill is rebuilt from scratch in T010; the old version currently calls the backend API which calls the SDK — the new version is the AI itself
- T020 requires a decision on how to display ranked jobs without the button — fetching `GET /api/jobs` and filtering by `fit_scored=true` client-side is the simplest approach
- `uv sync` in T016 will fail if `anthropic` is still in `pyproject.toml` — T006 must complete first
