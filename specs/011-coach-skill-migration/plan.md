# Implementation Plan: Coach Skill Migration

**Branch**: `011-coach-skill-migration` | **Date**: 2026-06-01 | **Spec**: [spec.md](spec.md)

## Summary

Remove the Anthropic SDK from the backend coach service and move all AI question generation into the `/coach-prep` Claude Code skill (runs under the Pro subscription at no per-token cost). The backend `POST /api/coach/prep` endpoint is simplified to accept a pre-formed question list and persist it — no SDK calls. The skill does the reasoning in-context and POSTs the result. The frontend and `InterviewSession` DB schema are unchanged.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript / Next.js 15 (frontend — no changes)

**Primary Dependencies**: FastAPI, SQLAlchemy (async), pydantic — `anthropic` package removed from `pyproject.toml`

**Storage**: SQLite via SQLAlchemy async; `InterviewSession` table unchanged

**Testing**: pytest (backend contract + unit tests); Jest (frontend — no changes expected)

**Target Platform**: Local dev server (localhost:8000 backend, localhost:3000 frontend)

**Project Type**: Web service + Claude Code skill

**Performance Goals**: Prep pack POST roundtrip < 500ms (no AI call on backend path)

**Constraints**: Zero `import anthropic` in backend after migration; `make check` must pass

**Scale/Scope**: Single-user personal tool; no concurrency concerns

## Constitution Check

| Principle            | Status           | Notes                                             |
| -------------------- | ---------------- | ------------------------------------------------- |
| I. Test-First        | MUST comply      | Write failing tests before touching coach service |
| II. Code Quality     | MUST comply      | ruff + mypy strict; no function > 40 lines        |
| III. Self-Improvement| MUST comply      | `make check` stays green throughout               |
| IV. Simplicity       | MUST comply      | Coach service shrinks; no new abstractions        |
| V. Observability     | MUST comply      | Keep structured logging on POST /coach/prep       |
| VI. Cost-Conscious AI| **PRIMARY GOAL** | Removing SDK is the point of this feature         |

**Gate**: `grep -r "import anthropic" backend/` must return zero results after migration.

## Project Structure

### Documentation (this feature)

```text
specs/011-coach-skill-migration/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code changes

```text
backend/
├── pyproject.toml                          # remove anthropic>=0.105.0
├── uv.lock                                 # regenerated after dep removal
└── jobforce/
    ├── services/
    │   └── coach.py                        # gutted: remove SDK calls; accept pre-formed questions
    └── routers/
        └── coach.py                        # PrepRequest gains `questions` field; drop generate_prep_pack import

backend/tests/
└── contract/
    └── test_coach.py                       # update: remove mock patches; test real DB persistence

.claude/skills/
└── coach-prep/
    └── SKILL.md                            # rewrite: skill generates questions in-context, POSTs to backend
```

**Structure Decision**: Web application (Option 2). Frontend unchanged. All changes are in backend service + skill.

## Complexity Tracking

No constitution violations.

---

## Phase 0: Research

*See [research.md](research.md)*

## Phase 1: Design & Contracts

*See [data-model.md](data-model.md) and [contracts/](contracts/)*
