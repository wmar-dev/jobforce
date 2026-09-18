# Feature Specification: Recruiter Notes

**Feature Branch**: `008-recruiter-notes`

**Created**: 2026-05-28

**Status**: Implemented

**Input**: User description: "There should be the ability to take notes in the web app to write notes from meetings with recruiters and additional research on the company."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Add Notes to a Job (Priority: P1)

A job seeker views a job listing and wants to record observations from a recruiter call or personal research. They open the job detail view, navigate to a notes section, and type their notes. The notes are saved automatically and persist across sessions.

**Why this priority**: This is the core value of the feature — capturing and retaining notes against a job. Without this, no other story is meaningful.

**Independent Test**: Can be fully tested by opening any job listing, typing a note, refreshing the page, and verifying the note is still visible.

**Acceptance Scenarios**:

1. **Given** a user is viewing a job listing, **When** they type text in the notes area and navigate away, **Then** the note is saved and visible the next time they open that job.
2. **Given** a job has no notes, **When** the user opens the notes section, **Then** an empty, ready-to-edit notes area is shown with placeholder guidance text.
3. **Given** a job already has notes, **When** the user opens the notes section, **Then** the existing notes are pre-populated for editing.

---

### User Story 2 - View Notes in Job List (Priority: P2)

A job seeker is scanning their job list and wants to quickly see which jobs have notes so they can prioritize follow-ups.

**Why this priority**: Discoverability of notes is high-value for day-to-day workflow but the feature still delivers value without it.

**Independent Test**: Can be fully tested by adding a note to one job, returning to the job list, and verifying that job is visually distinguished from jobs without notes.

**Acceptance Scenarios**:

1. **Given** a user has added notes to some jobs, **When** they view the job list, **Then** jobs with notes display a visible indicator (e.g., a note icon or snippet).
2. **Given** a user has no notes on any job, **When** they view the job list, **Then** no note indicators are shown.

---

### User Story 3 - Edit and Clear Notes (Priority: P3)

A job seeker wants to update their notes after a follow-up call or clear them entirely if the job is no longer relevant.

**Why this priority**: Notes must be mutable; this story ensures the full lifecycle (create, update, delete) is covered.

**Independent Test**: Can be fully tested by editing an existing note, saving, and verifying the updated content persists; and by clearing the note and verifying it is gone.

**Acceptance Scenarios**:

1. **Given** a job has existing notes, **When** the user edits the text and saves, **Then** the updated notes are persisted.
2. **Given** a job has existing notes, **When** the user clears all text and saves, **Then** the notes are removed and the job no longer shows a notes indicator.

---

### Edge Cases

- What happens when the user types an extremely long note (e.g., >10,000 characters)?
- How does the system handle simultaneous edits from two browser tabs open on the same job?
- What happens if the network is unavailable when the user tries to save a note?
- Are notes preserved when a job is archived or deleted?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow users to create or update a single free-text note on any job listing (upsert semantics — one note per job).
- **FR-002**: System MUST persist notes so they survive page refresh and re-login.
- **FR-003**: System MUST allow users to edit the note on a job listing by overwriting it in place.
- **FR-004**: System MUST allow users to clear the note on a job listing (setting it to empty removes the notes indicator).
- **FR-005**: System MUST display a visual indicator on job list entries that have notes.
- **FR-006**: System MUST associate notes with a specific job and the authenticated user (notes are private, not shared).
- **FR-007**: System MUST accept notes up to at least 5,000 characters in length.
- **FR-008**: System SHOULD auto-save notes without requiring an explicit save button, or provide a clearly visible save action.

### Key Entities

- **Job Note**: A single free-text block per job. Associated with a specific Job. Has a `created_at` timestamp (when first written) and an `updated_at` timestamp (when last edited). Only one note record exists per job; editing overwrites it in place. Requires a DB migration to add `updated_at` to the `meeting_notes` table.
- **Job**: Existing entity; gains a has-notes indicator derived from the presence of a non-empty Job Note.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can open a job, add a note, and have it persist within 3 seconds of finishing typing (auto-save) or a single explicit save action.
- **SC-002**: 100% of jobs with notes display a visible indicator in the job list view.
- **SC-003**: Notes survive browser refresh and re-authentication with no data loss.
- **SC-004**: Users can add, edit, and delete notes without leaving the job detail view.

## Clarifications

### Session 2026-05-28

- Q: Is the note for a job a single mutable text block (edited in place) or an append-only log of timestamped entries? → A: Single mutable text block per job, edited in place (upsert).
- Q: Should `updated_at` be tracked on the note (requires DB migration) or only `created_at`? → A: Add `updated_at` column; display as "last edited" in the UI.

## Assumptions

- Notes are private to the authenticated user — there is no sharing or collaboration requirement for v1.
- The web app already has an authenticated user session; no new auth flows are needed.
- The notes field is plain text only (no rich-text formatting, attachments, or markdown rendering) for v1.
- Mobile responsiveness follows the existing app conventions; no special mobile-first treatment is required for this feature.
- There is no notification or reminder functionality tied to notes in v1.
- Notes are scoped per job, not per company — a note lives on the job listing, not a separate company profile.
