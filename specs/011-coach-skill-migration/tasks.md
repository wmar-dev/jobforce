# Tasks: Coach Skill Migration

**Input**: Design documents from `specs/011-coach-skill-migration/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/coach-api.md

**Organization**: Tasks are grouped by user story. Each story is independently testable.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Remove the Anthropic SDK dependency and wire the updated `PrepRequest` shape so the backend is ready to receive pre-formed questions.

- [x] T001 Remove `anthropic>=0.105.0` from `backend/pyproject.toml` and run `uv sync` in `backend/` to regenerate `uv.lock`
- [x] T002 Delete `import anthropic` and `from anthropic.types import TextBlock` from `backend/jobforce/services/coach.py`
- [x] T003 Verify `make check` in `backend/` still passes (lint + typecheck) after removal

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Rewrite the coach service and router so the backend accepts a pre-formed question list. No AI calls on the backend path. Must complete before US1 and US2 skill/frontend work.

**⚠️ CRITICAL**: US1 skill cannot POST questions until this phase is complete.

- [x] T004 Rewrite `backend/jobforce/services/coach.py`: remove `generate_prep_pack`, `_build_prep_prompt`, `_parse_questions_response`, `_is_technical_role`, `_fallback_questions`; keep `get_session_summary_data`; replace `evaluate_answer` with a stub that returns `{"feedback": "Submit answers via mock interview mode.", "score": 0.0}` without any SDK call
- [x] T005 Add `QuestionIn` Pydantic model to `backend/jobforce/routers/coach.py` with fields: `id: str`, `category: str`, `text: str`, `source_url: str | None = None`, `leetcode_url: str | None = None`, `guidance: str | None = None`
- [x] T006 Update `PrepRequest` in `backend/jobforce/routers/coach.py` to add required field `questions: list[QuestionIn]`
- [x] T007 Rewrite `post_prep` handler in `backend/jobforce/routers/coach.py`: validate job exists (404 if not), create `InterviewSession` directly from `body.questions` (no call to `generate_prep_pack`), return `PrepSessionOut`
- [x] T008 Update `backend/tests/contract/test_coach.py`: remove all `patch("jobforce.routers.coach.generate_prep_pack", ...)` mocks; update `test_coach_prep_returns_session_with_all_four_categories` and `test_coach_prep_coding_question_has_leetcode_url` to POST questions directly in the request body; update `test_submit_answer_returns_feedback_and_score` to remove `evaluate_answer` mock (stub always returns)
- [x] T009 Run `cd backend && make check` — all gates must pass (lint, typecheck, tests, zero `import anthropic`)

**Checkpoint**: `POST /api/coach/prep` with `{job_id, questions}` creates a session and returns it. `make check` green.

---

## Phase 3: User Story 1 — Generate Prep Pack via Skill (Priority: P1) 🎯 MVP

**Goal**: The `/coach-prep` skill fetches job details, generates categorized questions using in-context Claude reasoning, and POSTs them to the backend — no API key required in the backend.

**Independent Test**: Run `/coach-prep <job_id>` in Claude Code; confirm output shows questions by category, then verify an `InterviewSession` row exists via `GET /api/coach/sessions` or the frontend.

### Implementation for User Story 1

- [x] T010 [US1] Rewrite `.claude/skills/coach-prep/SKILL.md`:
  - Step 1: `GET http://localhost:8000/api/jobs/{job_id}` to fetch title + description
  - Step 2: Detect technical role (title contains engineer/developer/architect/sre/devops/backend/frontend/fullstack/data/ml/ai/software)
  - Step 3: Using in-context Claude reasoning, generate questions for categories: always `behavioral` + `role_specific`; add `coding` + `system_design` for technical roles
  - Step 4: Embed a static curated bank as a starting point — at minimum: 3 behavioral (STAR tips), 3 coding (real LeetCode URLs: two-sum, lru-cache, valid-parentheses), 2 system design, 2 role-specific — supplement with job-tailored questions
  - Step 5: `POST http://localhost:8000/api/coach/prep` with `{"job_id": <id>, "questions": [...]}`
  - Step 6: Display questions grouped by category with guidance tips and LeetCode links
  - Step 7: Print summary: total questions, LeetCode problems linked, session ID

**Checkpoint**: Running `/coach-prep <id>` produces formatted output and a persisted `InterviewSession`. No Anthropic API key prompt in the backend.

---

## Phase 4: User Story 2 — Frontend Displays Skill-Generated Session (Priority: P2)

**Goal**: Confirm the frontend coach page loads and displays skill-generated sessions without any code changes. This phase is verification only.

**Independent Test**: After running `/coach-prep <job_id>`, open `http://localhost:3000/coach`, select the job, and confirm questions appear by category.

### Implementation for User Story 2

- [x] T011 [US2] Start backend and frontend (`make dev` from repo root) and run `/coach-prep <job_id>` for a real job
- [x] T012 [US2] Open `http://localhost:3000/coach` in browser, select the job, click "Generate Prep Pack" — confirm the session from the skill appears (questions display in all populated categories, category filter buttons appear, no console errors)
- [x] T013 [US2] If any frontend fetch or rendering issue is found, fix it in `frontend/src/app/coach/page.tsx` or `frontend/src/lib/api.ts`; otherwise mark as no-change needed

**Checkpoint**: Frontend displays skill-generated sessions correctly end-to-end.

---

## Phase 5: User Story 3 — Built-in Example Questions with LeetCode URLs (Priority: P3)

**Goal**: The static question bank in the skill includes curated examples with real LeetCode URLs for coding and STAR-method guidance for behavioral — these are embedded in the skill, not fetched.

**Independent Test**: Run `/coach-prep` for any job and verify: ≥2 coding questions each with a valid LeetCode URL, ≥1 behavioral question with STAR tip, ≥1 system design question.

### Implementation for User Story 3

- [x] T014 [US3] Audit the static question bank in `.claude/skills/coach-prep/SKILL.md` added in T010; expand it to include at minimum:
  - Behavioral: "Tell me about a time you…" (failure, leadership, conflict) — STAR guidance on each
  - Coding: LRU Cache (`https://leetcode.com/problems/lru-cache/`), Valid Parentheses (`https://leetcode.com/problems/valid-parentheses/`), Two Sum (`https://leetcode.com/problems/two-sum/`), Merge Intervals (`https://leetcode.com/problems/merge-intervals/`)
  - System Design: Rate limiter (token bucket tip), URL shortener (hashing tip)
  - Role-specific: 2 generic templates using job title
- [x] T015 [US3] Run `/coach-prep` against a technical job and a non-technical job; confirm coding/system design questions absent for non-technical role

**Checkpoint**: All coding questions have LeetCode URLs. Non-technical roles get only behavioral + role-specific.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [x] T016 [P] Update skill description in `.claude/skills/coach-prep/SKILL.md` frontmatter: change description from "AI-powered" to "Claude Code–powered (no API key required)"
- [x] T017 [P] Update `CLAUDE.md` "Current Feature Context" section to reflect feature 011 complete and the `anthropic` package removed
- [x] T018 Run `cd backend && make check` one final time — confirm zero `import anthropic`, lint clean, all tests pass
- [x] T019 Verify `grep -r "import anthropic" backend/` returns zero results

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks Phase 3 and Phase 4**
- **Phase 3 (US1 Skill)**: Depends on Phase 2 (backend must accept pre-formed questions)
- **Phase 4 (US2 Frontend)**: Depends on Phase 3 (need a skill-generated session to verify)
- **Phase 5 (US3 Question Bank)**: Depends on Phase 3 (expands the bank added in T010)
- **Phase 6 (Polish)**: Depends on all phases complete

### User Story Dependencies

- **US1 (P1)**: After Phase 2 — no dependency on US2 or US3
- **US2 (P2)**: After US1 — needs a skill-generated session to verify frontend
- **US3 (P3)**: After US1 — expands the bank embedded in T010

### Within Each Phase

- T001 → T002 → T003 (sequential: remove dep, then verify)
- T004 → T005 → T006 → T007 → T008 → T009 (sequential: service before router before tests)
- T010 is the single US1 task (rewrite SKILL.md)
- T011 → T012 → T013 (sequential: run skill, open UI, fix if needed)
- T014 → T015 (sequential: expand bank, then verify non-technical path)

---

## Parallel Opportunities

```bash
# Phase 6 — T016 and T017 can run in parallel (different files):
Task: "Update skill frontmatter description in .claude/skills/coach-prep/SKILL.md"
Task: "Update CLAUDE.md Current Feature Context"
```

---

## Implementation Strategy

### MVP First (US1 Only)

1. Complete Phase 1: Remove SDK dep
2. Complete Phase 2: Rewrite backend coach service + update tests
3. Complete Phase 3 (T010): Rewrite skill
4. **STOP and VALIDATE**: Run `/coach-prep <id>`, confirm session created, `make check` green
5. Ship MVP — coach works, zero backend API spend

### Incremental Delivery

1. Phase 1 + 2 → Backend ready, tests green
2. Phase 3 → Skill generates and persists sessions → MVP done
3. Phase 4 → Frontend verified end-to-end
4. Phase 5 → Question bank enriched with curated examples
5. Phase 6 → Polish and documentation

---

## Notes

- No new files are created — only modifications to existing files
- The `InterviewSession` DB schema is untouched — no migration needed
- Mock interview / answer evaluation is intentionally stubbed, not removed, to preserve the frontend contract
- The skill is the only AI-reasoning component post-migration
