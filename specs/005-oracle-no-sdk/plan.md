# Implementation Plan: Oracle SDK-Free Job Ranking

**Branch**: `005-oracle-no-sdk` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-oracle-no-sdk/spec.md`

## Summary

Replace the Anthropic SDK call in `backend/jobforce/services/oracle.py` with a
Claude Code skill that fetches job and profile data from the backend API, performs
fit scoring itself, and writes results back via a new score-write endpoint. The
backend becomes a dumb data store for Oracle; all AI reasoning happens inside
Claude Code sessions billed to the subscription.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/React (frontend), Markdown
(Claude Code skill)

**Primary Dependencies**: FastAPI (backend router), SQLAlchemy async (ORM),
pytest + httpx (test suite). No new dependencies added — `anthropic` package
removed.

**Storage**: SQLite via SQLAlchemy; existing `job_listings` table columns
(`fit_score`, `fit_scored`, `fit_confidence`, `fit_rationale`) are reused unchanged.

**Testing**: pytest (existing contract test suite); tests already mock `rank_jobs`
at the router level so they survive the service rewrite without modification.

**Target Platform**: Developer local environment (FastAPI backend + Next.js
frontend + Claude Code CLI).

**Project Type**: Internal developer tooling — backend service + CLI skill.

**Performance Goals**: Score up to 10 jobs in under 60 seconds via the skill
(SC-002). No backend latency regression.

**Constraints**:

- Zero `anthropic` imports anywhere in application or test code (FR-001, SC-001).
- Scores stored as 0.0–1.0 float — no conversion in the write path (clarification A).
- Existing tests must pass 100% after the change (SC-004).

**Scale/Scope**: Single developer, local environment. One service file rewritten,
one router endpoint added, one skill file updated.

## Constitution Check

| Principle | Status | Notes |
| --- | --- | --- |
| I. Test-First Development | ✅ Pass | New score-write endpoint gets a contract test before implementation |
| II. Code Quality Standards | ✅ Pass | Deleting SDK code reduces complexity; new endpoint is trivially simple |
| III. Self-Improvement Loop | ✅ Pass | Removes a constitution violation — direct improvement |
| IV. Simplicity & Clarity | ✅ Pass | oracle.py becomes simpler (no async client, no prompt building) |
| V. Observability & Feedback | ✅ Pass | Existing logging preserved; skill prints per-job results |
| VI. Cost-Conscious AI Usage | ✅ Pass | SDK removed; all AI reasoning via Claude Code subscription |

No violations. Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/005-oracle-no-sdk/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/
│   └── score-write-endpoint.md
└── tasks.md             # /speckit-tasks output
```

### Source Code changes

```text
backend/jobforce/services/
└── oracle.py            # MODIFIED: remove SDK; keep helpers; add rank_job_scores() stub

backend/jobforce/routers/
└── oracle.py            # MODIFIED: POST /oracle/score/{job_id} added; POST /oracle/rank kept (stub)

backend/pyproject.toml   # MODIFIED: remove anthropic>=0.28 dependency

backend/tests/contract/
└── test_oracle.py       # MODIFIED: add test for new score-write endpoint; existing tests unchanged

.claude/skills/
└── oracle-rank.md       # MODIFIED: full rewrite — fetch jobs+profile, reason, call score endpoint

frontend/src/app/oracle/
└── page.tsx             # MODIFIED: replace button with Claude Code instruction panel
```

## Complexity Tracking

> No violations — table not required.
