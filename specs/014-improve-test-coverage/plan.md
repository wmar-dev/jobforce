# Implementation Plan: Improve Test Coverage for Jobs Router and Coach Service

**Branch**: `014-improve-test-coverage` | **Date**: 2026-09-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/014-improve-test-coverage/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Backend test coverage for `jobforce/routers/jobs.py` (reported 62%) and `jobforce/services/coach.py`
(reported 48%) is being raised to ≥85% each. Phase 0 research (see [research.md](./research.md)) found that
most of the apparent gap is a coverage-measurement bug, not a testing gap: `pytest-cov`'s default tracer
doesn't follow SQLAlchemy's async-to-sync `greenlet` bridge on Python 3.12, so lines already exercised by the
existing test suite were being reported as uncovered. Adding `concurrency = ["greenlet", "thread"]` to
`backend/pyproject.toml`'s `[tool.coverage.run]` — with zero test changes — raises the true baseline to ~92%
(`jobs.py`) and ~76% (`coach.py`). The remaining genuine gaps — a handful of `GET /api/jobs` filter branches,
every 404/422 error path across the job detail/patch/delete/status/reparse/note endpoints, and
`coach.py`'s `evaluate_answer` / `get_session_summary_data` error and fallback branches — are closed with
targeted additions to the existing contract-test files, plus one new direct service-level test file for the
two `coach.py` branches that have no reachable API path (`overall_summary` is never written by any current
code path).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, SQLAlchemy 2.x (async, `aiosqlite` driver bridged via `greenlet`), pytest,
pytest-asyncio (`asyncio_mode = auto`), pytest-cov / coverage.py 7.16, httpx (`AsyncClient` + `ASGITransport`
for contract tests)

**Storage**: SQLite, one throwaway file-backed DB per test via the existing `db_engine`/`db_session`
fixtures in `backend/tests/conftest.py` — no new storage or schema

**Testing**: pytest, run via `uv run pytest` (`backend/tests/contract/`, `backend/tests/services/`); coverage
enforced via `pytest-cov` (`addopts = "--cov=jobforce --cov-report=term-missing"` in `pyproject.toml`)

**Target Platform**: Backend service only (no frontend/Chrome-extension changes); runs wherever the existing
`make check` / `uv run pytest` commands already run (macOS dev machine, CI if configured)

**Project Type**: Web service (FastAPI backend) inside the existing `jobforce` monorepo (`backend/` +
`frontend/` + `chrome-extension/`); this feature touches `backend/` only

**Performance Goals**: N/A — test-only feature, no runtime behavior or performance characteristics change

**Constraints**: Must not change any existing API contract, request/response shape, or business logic; must
not introduce or re-introduce any `anthropic` SDK import (CLAUDE.md invariant); must not regress coverage or
test results for any currently-passing module; the one coverage-config line change must not alter what
counts as covered for any other module in a way that hides a real gap (verified in research.md by comparing
before/after coverage for the two target files only, then confirming the full-suite `make check` run still
passes)

**Scale/Scope**: 2 source files under test (`backend/jobforce/routers/jobs.py`, ~452 lines;
`backend/jobforce/services/coach.py`, ~82 lines) + 1 one-line config change
(`backend/pyproject.toml`); test changes land in 2 existing files
(`backend/tests/contract/test_jobs.py`, `backend/tests/contract/test_coach.py`) plus 1 new file
(`backend/tests/services/test_coach.py`)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Checked against `.specify/memory/constitution.md` v1.1.0:

- **I. Test-First Development**: This feature is a test backfill for already-shipped code, not new
  production logic — there is no new behavior to drive with a failing test first. The one exception is the
  `pyproject.toml` coverage-config line, which has no logic to TDD. Compliant by nature of the feature; the
  gate that still applies (and is honored) is "coverage has not regressed" (spec.md SC-004).
- **II. Code Quality Standards**: No new functions/methods beyond test code; existing lint/type/complexity
  gates already pass for `jobs.py`/`coach.py` and are not touched. Compliant.
- **III. Self-Improvement Loop**: This feature *is* an instance of the required self-improvement loop —
  finding and fixing a tooling gap (coverage misconfiguration) that was silently understating quality
  signal. Directly compliant; worth noting in the project's retrospective artifact if one exists.
- **IV. Simplicity & Clarity**: New tests reuse existing fixtures/patterns (`test_client`, `db_session`,
  `_ingest` helper, the `tests/services/test_oracle.py` direct-service-call pattern) rather than inventing
  new test infrastructure. Compliant.
- **V. Observability & Feedback**: N/A — no new runtime logging paths introduced.
- **VI. Cost-Conscious AI Usage**: No `anthropic` SDK usage is added; `coach.py`'s AI-reasoning-free stub
  behavior (post feature-011) is exactly what's being tested, not changed. The
  `grep -r "import anthropic" backend/` invariant is re-verified in quickstart.md Step 4. Compliant.

No violations. Complexity Tracking table is not needed.

## Project Structure

### Documentation (this feature)

```text
specs/014-improve-test-coverage/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

No `contracts/` directory — see research.md Decision 3 (no new API surface is introduced by this feature).

### Source Code (repository root)

```text
backend/
├── jobforce/
│   ├── routers/
│   │   └── jobs.py              # under test — no logic changes expected
│   └── services/
│       └── coach.py             # under test — no logic changes expected
├── pyproject.toml                # [tool.coverage.run] gets `concurrency = ["greenlet", "thread"]`
└── tests/
    ├── contract/
    │   ├── test_jobs.py          # extended: filter/sort/note/404/422 cases (FR-001..FR-010)
    │   └── test_coach.py         # extended: evaluate_answer error paths (FR-012)
    └── services/
        └── test_coach.py         # new: direct db_session tests for overall_summary branches (FR-013)

frontend/            # untouched — out of scope
chrome-extension/     # untouched — out of scope
```

**Structure Decision**: Existing monorepo layout (`backend/` + `frontend/` + `chrome-extension/`) is
unchanged. This feature works entirely inside `backend/`, following the repo's existing test-layout
convention: contract tests (API-level, via the `test_client` fixture) live under `backend/tests/contract/`,
and direct service-level tests (bypassing the router, via the `db_session` fixture) live under
`backend/tests/services/`, matching the existing `tests/services/test_oracle.py` precedent.

## Complexity Tracking

*No violations — table not needed.*
