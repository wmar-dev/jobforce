# Feature Specification: Oracle and Forge Use Resume as Candidate Profile

**Feature Branch**: `007-oracle-forge-resume`

**Created**: 2026-05-28

**Status**: Draft

**Input**: User description: "Make oracle and forge be based off of resume.json"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Oracle ranks jobs using resume (Priority: P1)

When a user runs `/oracle-rank`, the ranking prompt sent to the AI includes the structured resume data from the base resume.

**Why this priority**: Oracle's scoring is only as good as the candidate profile it sees. The resume is richer and more structured than the sparse UserProfile fields, so plugging it in directly improves ranking quality immediately.

**Independent Test**: Run `/oracle-rank` against any job after seeding a base resume. The AI-generated rationale should reference specific skills, roles, and experience sections from the resume rather than generic text.

**Acceptance Scenarios**:

1. **Given** a base resume exists in the database, **When** the oracle ranking prompt is built, **Then** the candidate profile section contains the structured resume content
2. **Given** no base resume exists, **When** the oracle ranking prompt is built, **Then** the job is scored with `confidence: low` and a warning "No base resume configured"

---

### User Story 2 - Forge tailors from the base resume without requiring an explicit resume ID (Priority: P2)

When a user runs `/forge-tailor` for a job, the tailoring flow automatically uses the base resume without the user needing to look up or specify a resume ID.

**Why this priority**: Currently the `/forge-tailor` skill must pass `base_resume_id` explicitly. Defaulting to the base resume removes friction for the common case.

**Independent Test**: Run `/forge-tailor` against any job listing without specifying a resume ID. The skill should retrieve and tailor the base resume automatically.

**Acceptance Scenarios**:

1. **Given** a base resume exists, **When** the tailor endpoint is called without specifying a resume ID, **Then** the base resume is used as the source
2. **Given** no base resume exists, **When** the tailor endpoint is called, **Then** a clear error is returned indicating the user must first set up a base resume
3. **Given** a tailored resume already exists for a job, **When** `/forge-tailor` is run again, **Then** the base resume (not the prior tailored version) is always used as the source

---

### User Story 3 - Resume data drives both oracle and forge consistently (Priority: P3)

Changes to the base resume (via `PUT /resume/base` or by re-seeding from `config/resume.json`) are immediately reflected in subsequent oracle rankings and forge tailoring runs without any manual sync step.

**Why this priority**: Data consistency across features prevents the profile from drifting out of sync.

**Independent Test**: Update `config/resume.json`, restart the server (which re-seeds), then run both `/oracle-rank` and `/forge-tailor`. Both should reflect the updated resume content.

**Acceptance Scenarios**:

1. **Given** the base resume is updated, **When** oracle ranking runs next, **Then** the new resume content is used in the prompt
2. **Given** the base resume is updated, **When** forge tailoring runs next, **Then** the new resume content is the tailoring source

---

### Edge Cases

- What happens when `config/resume.json` exists but contains invalid JSON? The seed step should log a warning and skip rather than crashing startup.
- What happens when the base resume's `structured_data` is empty or malformed? Oracle scores with `confidence: low` and a warning; forge returns a 404 with a descriptive error.
- What if no base resume exists? Oracle scores with `confidence: low` and warning "No base resume configured"; forge returns a 404 with a helpful message.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The oracle ranking prompt MUST use the base resume's structured data as the candidate profile when a base resume exists in the database.
- **FR-002**: When no base resume exists, oracle MUST score the job with `confidence: low` and include a warning "No base resume configured" — no fallback to other data sources.
- **FR-003**: The forge tailor endpoint MUST accept a request without an explicit `base_resume_id` and resolve to the base resume automatically.
- **FR-004**: The forge tailor endpoint MUST return a clear 404 error when no base resume exists.
- **FR-005**: The `/forge-tailor` skill MUST NOT require the user to manually look up or provide a resume ID for the common tailoring flow.
- **FR-006**: The oracle profile-building function MUST accept a `Resume` object and produce a profile string from `structured_data`.
- **FR-007**: The forge `POST /resume/tailor` endpoint accepts pre-tailored `structured_data` from the skill; `base_resume_id` is no longer part of the request contract.

### Key Entities

- **Resume**: Structured candidate resume stored in the database (`is_base=1` marks the canonical source). Contains `structured_data` as a JSON string.
- **JobListing**: The job being ranked or tailored against.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Oracle ranking rationales reference at least one specific detail (skill, role title, or company) from the resume for 100% of scored jobs when a base resume exists.
- **SC-002**: The `/forge-tailor` skill completes a full tailor-and-export cycle without the user supplying a resume ID.
- **SC-003**: Both skills (`/oracle-rank`, `/forge-tailor`) and the backend service layer are updated consistently; no residual references to UserProfile remain anywhere in the codebase.
- **SC-004**: Startup with a missing or malformed `config/resume.json` produces a logged warning and completes without an exception.

## Assumptions

- The `Resume` model and `is_base` flag are already in place (implemented in prior work).
- `config/resume.json` seeding into the database is already wired up.
- UserProfile has been fully removed from the codebase; there is no fallback to it anywhere.
- The `/forge-tailor` skill performs AI tailoring itself (no backend SDK calls); it POSTs the resulting `structured_data` to `POST /resume/tailor` for storage.
- PDF rendering and LaTeX availability are out of scope for this feature.
- Multi-resume support (selecting from multiple saved resumes) is out of scope; this feature only concerns the single base resume.

## Clarifications

### Session 2026-05-28

- Q: What should oracle do when no base resume exists? → A: Score with `confidence: low` and warning "No base resume configured" — no fallback to other data sources.
