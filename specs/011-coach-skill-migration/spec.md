# Feature Specification: Coach Skill Migration

**Feature Branch**: `011-coach-skill-migration`

**Created**: 2026-06-01

**Status**: Draft

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Generate Interview Prep Pack via Skill (Priority: P1)

As a job seeker preparing for an interview, I want to run a Claude Code skill that generates a tailored set of interview questions for a specific job listing, so I can study without incurring per-token API costs.

**Why this priority**: This is the core coaching value. Removing the SDK dependency while preserving question generation is the primary goal.

**Independent Test**: Run `/coach-prep <job_id>` in Claude Code against a real job listing. The skill returns categorized questions with guidance tips and coding links — no Anthropic API key required in the backend.

**Acceptance Scenarios**:

1. **Given** a valid job ID exists in Jobforce, **When** the user runs `/coach-prep <job_id>`, **Then** the skill displays a set of questions organized by category (behavioral, role-specific, and coding/system design for technical roles) with guidance tips.
2. **Given** a technical role (contains "engineer", "developer", etc.), **When** the skill runs, **Then** coding and system design questions are included with example problems.
3. **Given** a non-technical role, **When** the skill runs, **Then** only behavioral and role-specific questions are returned.
4. **Given** an invalid job ID, **When** the skill runs, **Then** a clear error message is shown and no session is created.

---

### User Story 2 - Persist Prep Session Without SDK Call (Priority: P2)

As a job seeker, I want the generated question set saved to the Jobforce database so the frontend coach page can still display my prep pack, without the backend making any Anthropic API calls.

**Why this priority**: The frontend coach UI depends on `InterviewSession` records. Saving the skill-generated questions preserves the existing UI without rework.

**Independent Test**: After running the skill, open the frontend `/coach` page and confirm the session and questions appear for that job.

**Acceptance Scenarios**:

1. **Given** the skill generates questions for a job, **When** it posts the questions to the backend, **Then** an `InterviewSession` row is created with `session_type="prep"` and the questions stored as JSON.
2. **Given** a session exists in the database, **When** the user visits the `/coach` page, **Then** questions are displayed correctly by category.

---

### User Story 3 - Built-in Example Questions by Category (Priority: P3)

As a job seeker, I want each question category to include curated example questions with LeetCode links (for coding) so I have concrete study material even before researching role-specific questions.

**Why this priority**: This replaces the Claude-generated questions with high-quality hardcoded examples, reducing variability and cost while still providing actionable prep material.

**Independent Test**: Run the skill for any job and verify that at least one coding question includes a valid LeetCode URL, and at least one behavioral question includes a STAR-method tip.

**Acceptance Scenarios**:

1. **Given** any job, **When** the skill generates questions, **Then** behavioral questions include STAR-method guidance.
2. **Given** a technical role, **When** the skill generates questions, **Then** at least 2 coding questions include LeetCode problem URLs.
3. **Given** a technical role, **When** the skill generates questions, **Then** at least 1 system design question is included with a design framework tip.

---

### Edge Cases

- What happens when the backend is unreachable when the skill runs? → Skill should display an error and not silently fail.
- What happens if the job has no title or description? → Skill defaults to behavioral + role-specific questions only (non-technical path).
- What if a session already exists for a job? → A new session is created each time (prep packs are not deduplicated).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The backend coach service MUST NOT call the Anthropic SDK for question generation or answer evaluation.
- **FR-002**: The `/coach-prep` Claude Code skill MUST fetch job details from the backend and generate interview questions using in-context Claude reasoning (Pro subscription, no extra cost).
- **FR-003**: The skill MUST categorize questions as: behavioral, role-specific, and (for technical roles) coding and system design.
- **FR-004**: Each coding question MUST include a LeetCode problem URL.
- **FR-005**: Each question MUST include a guidance tip to aid preparation.
- **FR-006**: The skill MUST POST the generated questions to the backend to create an `InterviewSession` record.
- **FR-007**: The backend MUST accept a pre-formed question list via API (no AI call on the backend side).
- **FR-008**: The frontend coach page MUST continue to display sessions created by the skill without modification.
- **FR-009**: The `anthropic` Python package import MUST be removed from the coach service.
- **FR-010**: The skill MUST include a curated bank of example questions per category as a baseline, supplemented by job-specific reasoning.

### Key Entities

- **InterviewSession**: Stores the prep pack for a job; `questions` field holds a JSON array of question objects. Created by the skill via backend API.
- **QuestionItem**: `{id, category, text, source_url, leetcode_url, guidance}` — unchanged schema.
- **CoachPrepSkill**: Claude Code skill (`.claude/skills/coach-prep/SKILL.md`) that replaces the SDK-driven backend logic.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Zero Anthropic API calls originate from the backend after this change — verifiable by `grep -r "import anthropic" backend/` returning no results outside `services/coach.py` (which is then deleted or emptied).
- **SC-002**: A prep pack for any job can be generated end-to-end in under 30 seconds via the skill.
- **SC-003**: The frontend coach page loads and displays a skill-generated session without errors.
- **SC-004**: Each generated prep pack contains at least 4 questions (1 per category minimum for technical roles, 2 for non-technical).
- **SC-005**: 100% of coding questions include a working LeetCode URL.

## Assumptions

- The user runs Claude Code with a Pro subscription, so skill-based Claude reasoning has no additional per-token cost.
- The existing frontend coach UI (`/coach` page, `QuestionCard`, `MockInterviewPanel`) requires no changes — it continues to read from `InterviewSession` records as before.
- The mock interview / answer evaluation feature (submit answer → get feedback) is out of scope for this migration; it can remain as a stub or be removed.
- The backend API endpoint `POST /api/coach/prep` will be kept but simplified to just accept and store a pre-formed question list rather than generating questions itself.
- Role detection logic (technical vs. non-technical based on title/description keywords) moves into the skill.
