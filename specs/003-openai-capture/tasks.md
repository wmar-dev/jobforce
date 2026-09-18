# Tasks: Chrome Extension Job Capture — Site Adapter Framework

**Input**: Design documents from `specs/003-openai-capture/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md)

**Organization**: TDD — tests written first, then implementation.

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [x] T001 Add Jest + jsdom to chrome-extension/: create chrome-extension/package.json with jest, jest-environment-jsdom, and test script

---

## Phase 2: Foundational

- [x] T002 Create chrome-extension/tests/adapters/ directory structure

---

## Phase 3: User Story 1 — Capture OpenAI Job (Priority: P1) 🎯 MVP

**Goal**: One-click capture of openai.com/careers/* returns title, "OpenAI", and location.

**Independent Test**: Run `npm test` in chrome-extension/ — all adapter tests pass.

### Tests (write first — confirm they fail)

- [x] T003 [US1] Write generic adapter tests in chrome-extension/tests/adapters/generic.test.js: h1 title, og:site_name company, data-location, role_type from body text
- [x] T004 [US1] Write OpenAI adapter tests in chrome-extension/tests/adapters/openai.test.js: company="OpenAI", slugToLocation san-francisco→"San Francisco", h1+p location, unknown slug→null
- [x] T005 [US1] Write integration test in chrome-extension/tests/content.test.js: OpenAI DOM → company="OpenAI"; generic DOM → same result as before (regression guard)

### Implementation

- [x] T006 [US1] Rewrite chrome-extension/content.js with adapter registry framework (ADAPTERS map, runAdapter, merge, genericAdapter, openaiAdapter, slugToLocation)

---

## Phase 4: User Story 2 — Graceful Partial Capture (Priority: P2)

**Goal**: Missing company/location still saves; no hard failure on partial data.

**Independent Test**: Generic DOM missing company_name → capture succeeds with empty string, no error thrown.

### Implementation

- [x] T007 [US2] Verify merge() returns empty string (not null/undefined) for missing company_name so background.js validation passes

---

## Phase 5: Polish & Verification

- [x] T008 Run `npm test` in chrome-extension/ — all tests pass
- [x] T009 Run `make check` from project root — no regressions in backend or frontend

---

## Dependencies & Execution Order

- T001 → T002 → T003/T004/T005 (parallel) → T006 → T007 → T008 → T009
- T003, T004, T005 can run in parallel (different files)

---

## Notes

- No bundler — content.js is a single plain JS file loaded directly by Chrome
- Tests run in jsdom (Node.js), not a real browser; chrome.* APIs are not tested here
- `make check` runs backend + frontend gates; chrome-extension tests run separately via `npm test` in chrome-extension/
