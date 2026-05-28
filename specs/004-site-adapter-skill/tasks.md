---
description: "Task list for Site Adapter Skill"
---

# Tasks: Site Adapter Skill

**Input**: Design documents from `specs/004-site-adapter-skill/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Not requested in spec. Manual end-to-end verification only (load extension in Chrome after adapter is written).

**Organization**: Tasks grouped by user story to enable independent implementation and delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup

**Purpose**: Confirm environment and project structure are ready.

- [x] T001 Verify Playwright MCP server is configured (`claude mcp list` shows `playwright`)
- [x] T002 Verify `chrome-extension/content.js` is at expected path and has the `ADAPTERS` registry structure intact

---

## Phase 2: Foundational

**Purpose**: Fix the confirmed regression in the existing `openaiAdapter` before adding new capabilities. All user stories depend on a correct baseline.

**⚠️ CRITICAL**: The existing `openaiAdapter` uses `h1 + p` for location selection but the live OpenAI careers page uses `h2` for the job title. This regression must be fixed before the skill is built.

- [x] T003 Fix `openaiAdapter` location selector in `chrome-extension/content.js`: change `h1 + p` → `main h2 + p` and verify title uses `main h2` not `h1`
- [x] T004 Fix `openaiAdapter` title selector in `chrome-extension/content.js` to use `main h2` (currently falls through to `genericAdapter` which uses `h1`)
- [x] T005 [P] Add compensation extractor to `openaiAdapter` in `chrome-extension/content.js` targeting the sidebar paragraph (selector: scan for paragraph preceded by `strong` containing "Compensation")

**Checkpoint**: Load the extension in Chrome, navigate to an OpenAI careers URL, trigger capture — confirm title, location, and compensation extract correctly.

---

## Phase 3: User Story 1 — Inspect and Capture Job Page Format (Priority: P1) 🎯 MVP

**Goal**: Skill navigates to a URL, extracts all available fields, and displays a structured field summary. No code changes made.

**Independent Test**: Run `/site-adapter-update <url>` — verify field summary is printed with correct values and `content.js` is NOT modified.

### Implementation for User Story 1

- [x] T006 [US1] Create skill file `.claude/skills/site-adapter-update.md` with the skill header, usage instructions, and the field extraction phase (Steps 1–3 only: navigate, snapshot, extract FieldSummary and display it)
- [x] T007 [P] [US1] Add input validation section to `.claude/skills/site-adapter-update.md`: handle missing URL argument (print usage and exit) and handle navigation failure (print error and exit)
- [x] T008 [P] [US1] Add field summary output format to `.claude/skills/site-adapter-update.md`: markdown table with all 6 fields (title, company_name, location, description truncated to 200 chars, compensation, role_type), show "(not found)" for missing fields, and show "Adapter exists: Yes / No"

**Checkpoint**: Run `/site-adapter-update https://openai.com/careers/software-engineer-ad-formats-san-francisco/` — verify field summary prints correctly and no files are modified.

---

## Phase 4: User Story 2 — Generate or Update Chrome Extension Adapter (Priority: P2)

**Goal**: After displaying the field summary, skill generates or updates the site-specific adapter in `content.js`.

**Independent Test**: Run `/site-adapter-update <url>` end-to-end — verify `content.js` is updated with a new or replaced adapter entry for the hostname, all other content unchanged.

### Implementation for User Story 2

- [x] T009 [US2] Add git guard step to `.claude/skills/site-adapter-update.md`: run `git diff --name-only chrome-extension/content.js` — if file is dirty, print warning and exit without writing
- [x] T010 [US2] Add adapter generation step to `.claude/skills/site-adapter-update.md`: using extracted FieldSummary, generate a SiteAdapter JS object containing only the fields that were successfully found (omit fields returning null/not found)
- [x] T011 [US2] Add content.js write step to `.claude/skills/site-adapter-update.md`: locate the `ADAPTERS` object literal in `chrome-extension/content.js`, replace the existing entry for the hostname if present, or insert a new entry if absent — preserve all other file content byte-for-byte
- [x] T012 [P] [US2] Add completion report step to `.claude/skills/site-adapter-update.md`: print hostname, file path, list of fields with site-specific extractors, and list of fields falling back to generic adapter

**Checkpoint**: Run `/site-adapter-update https://openai.com/careers/software-engineer-ad-formats-san-francisco/` — verify `content.js` contains an updated `openai.com` adapter entry, then run again to verify idempotency (no duplicate entry).

---

## Phase 5: User Story 3 — Skill Reusability Across Sites (Priority: P3)

**Goal**: Skill works correctly for any publicly accessible job board hostname, not just OpenAI.

**Independent Test**: Run the skill against two additional job board URLs (e.g., a Greenhouse or Lever posting) — verify distinct adapter entries are created in `ADAPTERS` and the `openai.com` entry is unchanged.

### Implementation for User Story 3

- [x] T013 [US3] Add hostname normalisation step to `.claude/skills/site-adapter-update.md`: strip `www.` prefix from URL hostname before using as the adapter key (e.g., `www.greenhouse.io` → `greenhouse.io`)
- [x] T014 [P] [US3] Add site-agnostic selector inference guidance to `.claude/skills/site-adapter-update.md`: instruct Claude to prefer semantic selectors (heading levels, ARIA roles, sibling relationships) over class names or nth-child, and to note in the completion report if any selectors used are fragile

**Checkpoint**: Run skill against a Greenhouse or Lever job URL — verify a new adapter entry is added without modifying the `openai.com` entry.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, edge case hardening, and final validation.

- [x] T015 [P] Add error handling guidance for non-job pages to `.claude/skills/site-adapter-update.md`: if title and company_name both return "(not found)", print a warning and ask developer to confirm before writing the adapter
- [x] T016 Update `specs/004-site-adapter-skill/quickstart.md` with any final usage notes discovered during implementation (especially any selector patterns that proved reliable across sites)
- [x] T017 Run full end-to-end validation per `specs/004-site-adapter-skill/quickstart.md`: OpenAI URL → field summary correct, adapter written, Chrome extension captures correctly

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — verify environment before starting
- **Foundational (Phase 2)**: Depends on Setup — fixes regression in existing code, MUST complete before Phase 3
- **US1 (Phase 3)**: Depends on Foundational — builds inspection-only MVP
- **US2 (Phase 4)**: Depends on US1 — adds write capability to the skill
- **US3 (Phase 5)**: Depends on US2 — extends to arbitrary hostnames
- **Polish (Phase 6)**: Depends on all story phases complete

### Within Each User Story

- Skill file steps must be added in workflow order (navigate → extract → display → guard → write → report)
- T009 (git guard) MUST be added before T011 (write step) — guard is a prerequisite of writing

### Parallel Opportunities

```bash
# Phase 3 — run in parallel after T006 is created:
T007  # input validation section
T008  # field summary output format

# Phase 4 — run in parallel after T011 is complete:
T012  # completion report step

# Phase 5 — run in parallel after T013:
T014  # selector inference guidance

# Phase 6 — run in parallel:
T015  # non-job page error handling
T016  # quickstart update
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational regression fix (T003–T005)
3. Complete Phase 3: Skill inspection MVP (T006–T008)
4. **STOP and VALIDATE**: Run `/site-adapter-update <url>` and confirm field summary is correct
5. Demo: developer can inspect any public job URL in seconds

### Incremental Delivery

1. Setup + Foundational → regression fixed, extension works correctly on OpenAI
2. User Story 1 → inspection skill MVP (read-only, no writes)
3. User Story 2 → full skill (inspection + adapter write)
4. User Story 3 → any job board supported
5. Polish → production-ready skill

---

## Notes

- [P] tasks operate on the same file (`.claude/skills/site-adapter-update.md`) but in distinct sections — parallelism is safe because each task adds a new section, not editing the same lines
- The skill file is built incrementally across phases — each phase adds new steps to the Markdown document
- All adapter JS changes (Phase 2) are in `chrome-extension/content.js`; all skill instruction changes (Phases 3–5) are in `.claude/skills/site-adapter-update.md` — these two files never conflict
- Verify tests fail before implementing → not applicable here (no automated tests; constitution exempts Markdown skill files from test-first requirement per research.md decision 6)
