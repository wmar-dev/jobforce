# Implementation Plan: Oracle and Forge Use Resume as Candidate Profile

**Branch**: `007-oracle-forge-resume` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/007-oracle-forge-resume/spec.md`

## Summary

Replace the sparse UserProfile as the candidate data source for Oracle and Forge with the structured base Resume. Remove UserProfile entirely. Move Forge's AI tailoring out of the backend SDK call and into the `/forge-tailor` skill (Constitution Principle VI compliance). The oracle ranking prompt and forge tailoring both read from `Resume.structured_data` (`is_base=1`).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: FastAPI, SQLAlchemy (async), Pydantic, Jinja2 (PDF rendering)

**Storage**: SQLite via SQLAlchemy — `resumes` table (`is_base=1` row is canonical)

**Testing**: pytest + pytest-asyncio

**Target Platform**: Local backend server (`cd backend && make dev`)

**Project Type**: Web service (FastAPI backend) + Claude Code skills

**Performance Goals**: No new latency constraints — oracle and forge are human-triggered, not automated

**Constraints**: Zero `anthropic` SDK imports anywhere in application code (Constitution VI)

**Scale/Scope**: Single-user personal tool; one base resume at a time

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Test-First | ⚠ Deferred | Feature is already implemented; tests to be added in tasks |
| II. Code Quality | ✅ | No functions exceed 40 lines; ruff/mypy clean |
| III. Self-Improvement Loop | ✅ | No regression patterns introduced |
| IV. Simplicity & Clarity | ✅ | UserProfile removed, single source of truth established |
| V. Observability | ✅ | Existing logging retained; warning emitted on missing resume |
| VI. Cost-Conscious AI | ✅ | `anthropic` import removed from `services/forge.py`; forge tailoring moved to skill |

**AI SDK Gate**: `grep -r "import anthropic" backend/` → zero results ✅

## Project Structure

### Documentation (this feature)

```text
specs/007-oracle-forge-resume/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (affected files)

```text
backend/
└── jobforce/
    ├── db/
    │   ├── models.py          # UserProfile class removed
    │   └── seed.py            # _seed_base_resume() added
    ├── routers/
    │   ├── forge.py           # POST /resume/tailor accepts structured_data from skill
    │   └── profile.py         # DELETED
    ├── services/
    │   ├── forge.py           # anthropic removed; tailor_resume() removed; compute_diff + render_pdf kept
    │   └── oracle.py          # _build_profile_text() now accepts Resume | None
    └── main.py                # profile router removed

.claude/skills/
├── oracle-rank/SKILL.md       # Step 3: fetches /api/resume/base instead of /api/profile
└── forge-tailor/SKILL.md      # AI tailoring moved here; posts structured_data to backend

config/
├── resume.json                # gitignored; seeded into DB on startup
└── resume.example.json        # committed template
```

## Complexity Tracking

No constitution violations. All changes reduce complexity (UserProfile removed, SDK dependency removed).

---

## Phase 0: Research

*No open unknowns — all decisions are constrained by existing architecture and Constitution VI.*

See [research.md](research.md) for consolidated findings.

## Phase 1: Design & Contracts

See [data-model.md](data-model.md) and [contracts/](contracts/) for entity and API contract details.
