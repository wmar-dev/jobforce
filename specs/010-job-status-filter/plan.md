# Implementation Plan: Job Status Filtering & Triage

**Branch**: `010-job-status-filter` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/010-job-status-filter/spec.md`

## Summary

Extend the job pipeline with two triage statuses — `archived` (dismissed, hidden by default) and `shortlisted` (intent to apply) — plus a bulk-archive action for low-score jobs. Changes touch: DB migration, backend model/transition graph/router, and frontend type definitions, status badge, job list tabs, job card actions, and Coach page filter.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / React 18 (frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy async, SQLite (backend); Next.js 15, SWR, Tailwind (frontend)

**Storage**: SQLite — requires table-recreate migration to update CHECK constraint

**Testing**: pytest + pytest-cov (backend); Jest (frontend)

**Target Platform**: Local dev (macOS), single-user

**Project Type**: Web application (FastAPI backend + Next.js frontend)

**Performance Goals**: Standard web app — status transitions are single-row updates, bulk archive is a single transaction

**Constraints**: SQLite CHECK constraint changes require table recreation; no Anthropic SDK usage (Constitution VI)

**Scale/Scope**: Single user, hundreds of job listings

## Constitution Check

| Principle | Status | Notes |
| --- | --- | --- |
| I. Test-First | MUST PASS — write failing tests before implementation | Tests for transition graph, bulk archive endpoint, default exclusion |
| II. Code Quality | MUST PASS — ruff, mypy strict, ≤40 lines/fn | New service function for bulk archive must stay simple |
| III. Self-Improvement | PASS — `make check` covers all gates | No new tooling needed |
| IV. Simplicity | PASS — extend existing pattern, no new abstractions | Reuse `transition_status()`, extend constants |
| V. Observability | PASS — status transitions already logged via `status_transitions` table | |
| VI. No AI SDK | PASS — no AI calls in this feature | |

No violations. Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/010-job-status-filter/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── api.md           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (files touched)

```text
backend/
├── jobforce/
│   ├── db/
│   │   ├── models.py                          # _VALID_STATUSES constant
│   │   └── migrations/
│   │       └── 010_add_triage_statuses.sql    # new migration
│   ├── routers/
│   │   └── jobs.py                            # bulk-archive endpoint; default exclusion
│   └── services/
│       └── scout.py                           # _VALID_TRANSITIONS + bulk_archive_low_score()
└── tests/
    ├── unit/
    │   └── test_triage_statuses.py            # transition graph unit tests
    └── integration/
        └── test_bulk_archive.py               # bulk archive endpoint integration tests

frontend/
└── src/
    ├── lib/
    │   ├── types.ts                           # PipelineStatus union type
    │   └── api.ts                             # bulkArchive() fetch wrapper
    ├── components/
    │   └── jobs/
    │       ├── StatusBadge.tsx                # archived + shortlisted entries
    │       └── JobTable.tsx                   # inline archive/shortlist action buttons
    └── app/
        ├── jobs/
        │   └── page.tsx                       # STATUS_TABS + VALID_STATUSES + "Active" rename
        └── coach/
            └── page.tsx                       # add shortlisted fetch
```
