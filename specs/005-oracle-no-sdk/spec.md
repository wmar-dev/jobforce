# Feature Specification: Oracle SDK-Free Job Ranking

**Feature Branch**: `005-oracle-no-sdk`

**Created**: 2026-05-27

**Status**: Implemented

**Input**: User description: "Fix Oracle, so it doesn't use anthropic sdk, give me some alternatives, particularly using claude code."

## Context

The Oracle feature currently scores job listings for fit against the user's
profile by calling the Anthropic SDK directly from the backend server. This
violates the project constitution (Principle VI: Cost-Conscious AI Usage) which
prohibits programmatic SDK calls. All AI reasoning must be delivered through
Claude Code's subscription interface, not billed per-token API calls.

## Clarifications

### Session 2026-05-27

- Q: Should the skill output scores as 0.0–1.0 or 0–100, and who owns normalisation? → A: Skill outputs 0.0–1.0 matching the existing DB column; backend writes directly with no conversion.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Rank Jobs via Claude Code Skill (Priority: P1)

A developer runs `/oracle-rank` (or `/oracle-rank 2 5 7` for specific jobs)
from within Claude Code. Claude reads the job data and user profile directly,
reasons about fit, and writes the scores back to the backend — all within a
single Claude Code session, no SDK calls made.

**Why this priority**: This is the primary replacement path. It delivers the
same user-facing outcome (ranked jobs with scores and rationale) using the
Claude Code subscription instead of per-token billing.

**Independent Test**: Run `/oracle-rank` in Claude Code with at least one job
that has a description. Verify scores appear in the Jobforce UI at
`/oracle` without the backend ever importing or calling the Anthropic SDK.

**Acceptance Scenarios**:

1. **Given** at least one active job listing with a description, **When** the
   user runs `/oracle-rank` in Claude Code, **Then** each job receives a fit
   score (0–100), a confidence level (high/medium/low), and a 1–2 sentence
   rationale, all persisted to the backend and visible in the Oracle UI.
2. **Given** the user runs `/oracle-rank` with no profile set up, **When** the
   skill executes, **Then** jobs are scored with a warning that no profile is
   configured, and scores are stored with `confidence: low`.
3. **Given** a job listing with fewer than 100 characters of description,
   **When** the skill scores it, **Then** the result is stored with a sparse-
   description warning and `confidence: low`.
4. **Given** the backend is not running, **When** the skill tries to fetch job
   data, **Then** a clear error is shown and no partial writes occur.

---

### User Story 2 - Remove SDK Dependency from Backend (Priority: P2)

The backend server no longer imports or references the Anthropic SDK. The
Oracle ranking endpoint either delegates to an external caller (Claude Code)
or is replaced by a simpler data-write endpoint that Claude Code calls after
doing the reasoning itself.

**Why this priority**: Eliminates the SDK violation at the source. Even if US1
is complete, leaving the SDK import in the backend is a constitution violation.

**Independent Test**: Run `grep -r "anthropic" backend/jobforce/` — the result
must be empty. Run the backend test suite — all tests pass.

**Acceptance Scenarios**:

1. **Given** the backend codebase, **When** searched for any `anthropic` import
   or reference, **Then** zero matches are found in application code.
2. **Given** the Oracle UI page, **When** the user clicks "Rank Jobs", **Then**
   the UI either triggers the Claude Code skill via a clear instruction, or
   shows a message explaining that ranking is done via `/oracle-rank` in Claude
   Code.
3. **Given** the existing `/oracle/rank` API endpoint, **When** it is called
   directly (without Claude Code), **Then** it either returns a helpful error
   explaining the new workflow, or it no longer exists and the UI no longer
   surfaces it.

---

### User Story 3 - Oracle UI Reflects New Workflow (Priority: P3)

The Oracle page in the frontend communicates clearly that ranking is done
through Claude Code, not by clicking a button that calls an internal AI
endpoint. Users understand the new workflow.

**Why this priority**: Without this, the UI has a broken "Rank Jobs" button
that no longer works, creating a confusing experience.

**Independent Test**: Open `/oracle` in the browser. The page should either
(a) not show a "Rank Jobs" button at all, or (b) show a non-functional button
replaced with an instruction to run `/oracle-rank` in Claude Code.

**Acceptance Scenarios**:

1. **Given** the Oracle page, **When** a user visits it, **Then** any ranking
   trigger clearly communicates that ranking is performed via Claude Code, not
   via a server-side button click.
2. **Given** jobs that have already been ranked, **When** a user visits the
   Oracle page, **Then** previously stored scores and rationale are displayed
   correctly regardless of how they were generated.

---

### Edge Cases

- What happens if `/oracle-rank` is run while the backend is mid-write for
  another ranking session? Each job is scored and written independently; a
  partial run does not corrupt previously stored scores.
- What happens if the user profile changes after scores are stored? Scores are
  not automatically invalidated — the user must re-run `/oracle-rank`.
- What happens if Claude Code's reasoning produces a score outside 0–100?
  The skill must clamp values and log a warning.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend MUST NOT import or reference the Anthropic SDK
  (`anthropic` package) anywhere in application or test code.
- **FR-002**: Job fit scoring MUST be performed by Claude Code (via a skill or
  headless invocation), not by the backend server process.
- **FR-003**: The `/oracle-rank` Claude Code skill MUST fetch job data and user
  profile from the backend API, reason about fit, and write scores back via
  the backend API — all within a single skill execution.
- **FR-004**: The skill MUST score each job with: a numeric fit score (0–100),
  a confidence label (high/medium/low), and a 1–2 sentence rationale.
- **FR-005**: The skill MUST handle missing profile (score with warning) and
  sparse descriptions (flag with low confidence) without crashing.
- **FR-006**: The backend MUST expose a write endpoint that accepts externally
  computed scores for a given job ID: `score` (float 0.0–1.0), `confidence`
  (string: high/medium/low), and `rationale` (string). The existing
  `PATCH /jobs/{id}` endpoint may be extended for this purpose.
- **FR-007**: The Oracle frontend page MUST clearly communicate the new
  ranking workflow so users are not confused by a non-functional button.
- **FR-008**: All existing ranked scores already stored in the database MUST
  remain visible and unaffected by this change.

### Key Entities

- **FitScore**: A computed record for a job listing containing numeric score
  (0–100), confidence (high/medium/low), rationale text, and optional warning.
- **RankingSession**: A single invocation of `/oracle-rank` that may score one
  or many job listings and writes each result independently.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero references to the Anthropic SDK exist in the backend
  codebase after this change is merged.
- **SC-002**: A developer can rank all active jobs via `/oracle-rank` in Claude
  Code and see scores in the UI within 60 seconds for up to 10 jobs.
- **SC-003**: 100% of existing job scores stored before this change remain
  readable and correctly displayed in the Oracle UI after the change.
- **SC-004**: The backend test suite passes with 100% of existing tests
  continuing to pass after the SDK is removed.
- **SC-005**: The Oracle UI page contains no broken or misleading call-to-action
  that implies ranking happens server-side.

## Assumptions

- The Claude Code subscription (used by the developer) covers all AI reasoning
  costs; no per-token billing is introduced.
- The existing backend API (FastAPI) is accessible at `localhost:8000` when the
  developer runs `/oracle-rank`.
- The `oracle-rank.md` skill file in `.claude/skills/` is the primary delivery
  vehicle; no new compiled binary or daemon is needed.
- The frontend Oracle page currently has a "Rank Jobs" button that triggers a
  backend API call — this button's behaviour must change.
- Scores are expressed as 0.0–1.0 throughout (matching the existing DB column).
  The skill outputs values in this range; the backend writes them directly with
  no conversion. The display layer converts to percentage for presentation only.
