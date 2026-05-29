# Implementation Plan: Recruiter Notes

**Branch**: `008-recruiter-notes` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-recruiter-notes/spec.md`

## Summary

Add a notes section to the job detail view so users can record free-text observations from recruiter meetings and company research. The `MeetingNote` DB model already exists and already carries an optional `job_listing_id` foreign key; this feature wires up the missing API endpoints on the jobs router and a notes UI panel on the job detail page. No schema migration is required — the column is already nullable in the existing table.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Next.js 14 (frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy 2 async, Pydantic v2, aiosqlite (backend); Next.js, React, SWR, Tailwind CSS, Radix UI, Lucide React (frontend)

**Storage**: SQLite via aiosqlite (existing `meeting_notes` table, `job_listing_id` column already present)

**Testing**: pytest + pytest-asyncio (backend contract tests); no automated frontend tests in current project

**Target Platform**: Local web app (Python backend on localhost:8000, Next.js frontend on localhost:3000)

**Project Type**: Web application (backend API + frontend SPA)

**Performance Goals**: Standard web app — notes save and appear within one round-trip; no special throughput requirements

**Constraints**: No per-token AI SDK calls (Constitution VI); all AI capability through Claude Code CLI only

**Scale/Scope**: Single-user local tool; no multi-tenancy or auth required

## Constitution Check

| Gate                       | Status    | Notes                                                                                    |
| -------------------------- | --------- | ---------------------------------------------------------------------------------------- |
| Tests first (Principle I)  | MUST PASS | Contract tests for new endpoints written before implementation                           |
| Code quality (Principle II)| MUST PASS | ruff lint zero warnings, type annotations on all public functions, functions ≤ 40 lines  |
| Simplicity (Principle IV)  | MUST PASS | Reuse existing `MeetingNote` model and company-notes pattern; no new abstractions        |
| No AI SDK (Principle VI)   | N/A       | Feature has no AI component                                                              |
| All quality gates          | MUST PASS | `make check` passes before PR                                                            |

**No violations anticipated.** The `job_listing_id` column already exists — no migration complexity. The router and frontend patterns are already established in `companies.py` and `app/companies/[id]/page.tsx`.

## Project Structure

### Documentation (this feature)

```text
specs/008-recruiter-notes/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/           ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── jobforce/
│   ├── db/
│   │   └── models.py            # MeetingNote already has job_listing_id — no change needed
│   └── routers/
│       └── jobs.py              # ADD: GET /api/jobs/{id}/note, PUT /api/jobs/{id}/note, DELETE /api/jobs/{id}/note
└── tests/
    └── contract/
        └── test_jobs.py         # ADD: notes endpoint contract tests

frontend/
└── src/
    ├── app/
    │   └── jobs/
    │       └── [id]/
    │           └── page.tsx     # ADD: Notes section panel
    ├── components/
    │   └── jobs/
    │       └── JobTable.tsx     # ADD: notes indicator (note icon) on rows with notes
    ├── hooks/
    │   └── useJobNotes.ts       # ADD: SWR hook for job notes
    └── lib/
        ├── api.ts               # ADD: getJobNote, upsertJobNote, deleteJobNote
        └── types.ts             # ADD: JobNote type
```

**Structure Decision**: Follows existing Option 2 (Web application) layout already in use. New files mirror the company-notes pattern exactly.

## Complexity Tracking

> No constitution violations anticipated for this feature.
