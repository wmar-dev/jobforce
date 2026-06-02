# Feature Specification: Job Status Filtering & Triage

**Feature Branch**: `010-job-status-filter`

**Created**: 2026-06-01

**Status**: Draft

**Input**: User description: "I need a state for jobs that have low score, so I can ignore them, but keep track that I have crawled them. Having to many jobs in saved is overwhelming. I will only apply to a few jobs per company, so i need a way to mark the the jobs."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Archive Low-Score Jobs (Priority: P1)

After Oracle ranks jobs, the user wants to dismiss low-scoring listings from the active view without deleting them, so the pipeline stays clean while preserving the crawl history.

**Why this priority**: The core pain point — too many low-relevance jobs cluttering the saved list — is addressed directly here. This is the minimum viable fix.

**Independent Test**: Can be tested by marking a job as "archived" and confirming it disappears from the default job list but remains retrievable via a filtered view.

**Acceptance Scenarios**:

1. **Given** a job listing exists in the saved list, **When** the user marks it as "archived", **Then** it is removed from the default active job view and placed in an archived state.
2. **Given** a job is archived, **When** the user views the archived jobs list, **Then** the job appears with its original data and crawl timestamp intact.
3. **Given** a low fit_score job is crawled again, **When** it already exists in the system as archived, **Then** the system does not re-add it as a new saved job.

---

### User Story 2 - Mark Jobs to Apply To (Priority: P2)

The user wants to select a small set of jobs per company to pursue, so they can focus their effort on the most promising applications.

**Why this priority**: Without a way to flag "apply to this one," the user has no actionable shortlist even after removing low-score clutter.

**Independent Test**: Can be tested by marking one job per company as "shortlisted" and confirming those jobs appear in a dedicated shortlist or are visually distinguished in the job list.

**Acceptance Scenarios**:

1. **Given** a job listing exists, **When** the user marks it as "shortlisted", **Then** it is visually distinguished in the job list and accessible via a shortlist filter.
2. **Given** multiple jobs exist for the same company, **When** the user shortlists one, **Then** the other jobs for that company remain in their current state (saved or archived).
3. **Given** a shortlisted job, **When** the user removes the shortlist mark, **Then** the job returns to the default "saved" state.

---

### User Story 3 - Bulk Archive by Score Threshold (Priority: P3)

The user wants to quickly archive all jobs below a certain fit score in one action, rather than individually dismissing each one.

**Why this priority**: Convenience improvement after the core archive feature exists. Saves time when many low-score jobs accumulate.

**Independent Test**: Can be tested by triggering a bulk archive action with a score threshold and confirming all jobs below that threshold transition to archived state.

**Acceptance Scenarios**:

1. **Given** multiple jobs with varying fit scores exist, **When** the user triggers bulk archive with a score threshold, **Then** all jobs with fit_score below the threshold are archived.
2. **Given** a bulk archive is triggered, **When** some jobs are already shortlisted, **Then** shortlisted jobs are NOT archived regardless of their score.

---

### Edge Cases

- What happens when a job has no fit_score yet (not yet ranked by Oracle)? It should not be affected by score-based bulk archive.
- How does the system handle a job transitioning from "archived" back to "saved"? It should be supported via a restore action.
- What if the user shortlists a job that was previously archived? Shortlisting should implicitly restore it to active.
- What happens when a crawled job URL already exists as archived? The system should recognize it as already processed and not re-ingest it as new.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support an "archived" status for job listings that removes them from the default active view while preserving all crawl data.
- **FR-002**: System MUST support a "shortlisted" status for job listings that flags them as jobs the user intends to apply to.
- **FR-011**: Archive and shortlist actions MUST be accessible as inline buttons on each job card in the list view, requiring no navigation to a detail view.
- **FR-003**: Users MUST be able to transition a job from any status (saved, archived) to shortlisted.
- **FR-004**: Users MUST be able to archive a job from the saved or shortlisted state.
- **FR-005**: Users MUST be able to restore an archived job back to saved status.
- **FR-006**: The default job list view MUST exclude archived jobs unless the user explicitly filters to show them.
- **FR-007**: A shortlist view or filter MUST display only shortlisted jobs, grouped or filterable by company.
- **FR-008**: System MUST prevent duplicate ingestion of a job URL that already exists in any status (including archived).
- **FR-009**: System MUST support bulk archive of all jobs with fit_score below 50, excluding shortlisted jobs from bulk operations.
- **FR-010**: All status transitions MUST be recorded in the existing audit trail (status_transitions table).
- **FR-012**: The Coach page MUST include shortlisted jobs alongside applied and interviewing jobs.

### Key Entities

- **Job Listing**: Gains an expanded status field supporting values: `saved`, `archived`, `shortlisted` (in addition to existing pipeline statuses `applied`, `interviewing`, etc.).
- **Status Transition**: Records each status change with timestamp and previous/new status for audit purposes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The default job list shows only actionable jobs (saved + shortlisted); users do not need to scroll past archived entries.
- **SC-002**: A user can archive a low-score job in one action (single click/tap) from the job list.
- **SC-003**: A user can shortlist a job in one action from the job list.
- **SC-004**: Bulk archive archives all jobs with fit_score below 50 (excluding shortlisted) in a single operation.
- **SC-005**: Re-crawling an already-archived job URL does not create a duplicate entry or change the archived status.
- **SC-006**: The shortlist view shows jobs grouped by company, allowing the user to see at a glance how many jobs per company they plan to pursue.

## Clarifications

### Session 2026-06-01

- Q: What fit_score threshold does bulk archive use — fixed default, user-specified, or configurable? → A: Fixed default of 50 (jobs with fit_score < 50 are archived).
- Q: Where do archive and shortlist actions appear in the UI? → A: Inline action buttons on each job card in the list view.
- Q: Should shortlisted jobs appear on the Coach page alongside applied and interviewing? → A: Yes — shortlisted jobs appear on the Coach page.

## Assumptions

- The existing `status` field on `job_listings` will be extended; no new table is needed for statuses.
- "Archived" is a terminal triage state — it means "seen and dismissed," not deleted. Data is fully preserved.
- "Shortlisted" sits in the active pipeline before "applied" — it represents intent to apply but not yet applied.
- The existing pipeline statuses (`applied`, `interviewing`, `offer`, `rejected`) are unaffected by this feature.
- The Coach page filter is expanded to include `shortlisted` in addition to `applied` and `interviewing`.
- Bulk archive by score threshold is triggered manually by the user, not automatically on crawl.
- Mobile support is out of scope; UI changes target the existing Next.js dashboard only.
- The fit_score is set by the Oracle skill; jobs without a score are treated as unscored and excluded from score-based bulk operations.
