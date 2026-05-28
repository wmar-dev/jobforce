# Tasks: Scout Crawl Deterministic Parser

**Input**: Design documents from `specs/006-scout-crawl-parser/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, quickstart.md ✅

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies and create the new module skeleton before any feature work begins.

- [x] T001 Add `beautifulsoup4>=4.12`, `lxml>=5.0`, `playwright>=1.44` to `backend/pyproject.toml` dependencies and run `uv sync` in `backend/`
- [x] T002 Run `uv run playwright install chromium` in `backend/` to install the headless browser binary
- [x] T003 Create `backend/jobforce/cli/__init__.py` (empty, makes `cli` a package)
- [x] T004 [P] Register `jobforce.cli` in `packages` list in `backend/pyproject.toml` so it is importable via `uv run python -m jobforce.cli.*`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: The `parse.py` service is shared by both user stories. It must exist and be tested before either story's CLI or skill work begins.

**⚠️ CRITICAL**: Phases 3 and 4 both depend on this phase being complete.

- [x] T005 Write failing unit tests for `parse_html()`, `run_adapter()`, `merge()`, and `slug_to_location()` using static HTML fixtures in `backend/tests/unit/test_parse_service.py` — confirm all tests fail before proceeding
- [x] T006 [P] Create static HTML fixture files for the OpenAI adapter tests in `backend/tests/fixtures/openai_job.html` and `backend/tests/fixtures/generic_job.html`
- [x] T007 Implement `slug_to_location(pathname: str) -> str | None` in `backend/jobforce/services/parse.py` — port of `slugToLocation()` from `chrome-extension/content.js`
- [x] T008 Implement `GENERIC_ADAPTER` dict in `backend/jobforce/services/parse.py` with field extractor functions for `title`, `company_name`, `location`, `description`, `role_type` using BeautifulSoup CSS selectors matching `chrome-extension/content.js` `genericAdapter`
- [x] T009 Implement `SITE_ADAPTERS` dict in `backend/jobforce/services/parse.py` with `openai.com` adapter matching `chrome-extension/content.js` `openaiAdapter` (fields: `company_name`, `title`, `location`, `description`, `compensation`)
- [x] T010 Implement `run_adapter(adapter: dict, doc: BeautifulSoup, url: str) -> dict` in `backend/jobforce/services/parse.py` — calls each field fn, catches per-field errors, returns partial dict
- [x] T011 Implement `merge(base: dict, override: dict) -> dict` in `backend/jobforce/services/parse.py` — override wins when non-null and non-empty string
- [x] T012 Implement `parse_html(html: str, url: str) -> dict` public entry point in `backend/jobforce/services/parse.py` — resolves hostname, runs generic + site adapter, merges, returns ParseResult dict
- [x] T013 Run `backend/tests/unit/test_parse_service.py` and confirm all tests pass; run `ruff` and `mypy` on `backend/jobforce/services/parse.py`

**Checkpoint**: `parse.py` is complete, tested, and passing quality gates — story phases can now begin.

---

## Phase 3: User Story 1 — Capture Job via Scout Crawl with Structured Parsing (Priority: P1) 🎯 MVP

**Goal**: `/scout-crawl <URL>` invokes a single CLI tool that fetches the page headlessly, parses it deterministically, and posts structured fields to the ingest API — no LLM field inference.

**Independent Test**: Run `/scout-crawl https://openai.com/careers/3d-printing-lab-technician-robotics-san-francisco/` and verify `title`, `company_name`, `location`, `role_type`, and `description` exactly match the page content without variance across repeated runs.

### Implementation for User Story 1

- [x] T014 [US1] Write failing unit test for `scout_fetch` CLI timeout behaviour (30-second hard limit) in `backend/tests/unit/test_scout_fetch.py` — confirm test fails before proceeding
- [x] T015 [US1] Implement `backend/jobforce/cli/scout_fetch.py` — async entrypoint using `async_playwright`, navigates to `--url`, waits for `networkidle`, enforces 30-second hard timeout (exit code 1 + stderr message on timeout), grabs `document.documentElement.outerHTML`, calls `parse_html()`, prints JSON to stdout
- [x] T016 [US1] Run `backend/tests/unit/test_scout_fetch.py` and confirm timeout test passes; run `ruff` and `mypy` on `backend/jobforce/cli/scout_fetch.py`
- [x] T017 [US1] Update `.claude/skills/scout-crawl/SKILL.md` — replace MCP browser navigation steps and LLM field extraction with: (1) run `cd backend && uv run python -m jobforce.cli.scout_fetch --url <URL>`, (2) parse stdout JSON, (3) POST fields directly to `http://localhost:8000/api/ingest`
- [x] T018 [US1] Update `specs/006-scout-crawl-parser/quickstart.md` to reflect the new single-command invocation pattern

**Checkpoint**: `/scout-crawl <URL>` works end-to-end for any public job URL. Fields are deterministic across repeated runs.

---

## Phase 4: User Story 2 — Parsing Logic Reuses Chrome Extension Adapter Design (Priority: P2)

**Goal**: The Python parser and Chrome extension produce identical field values for the same URL on supported sites, and adding a new adapter requires editing only `parse.py`.

**Independent Test**: Run the parser against an OpenAI job URL with both the Chrome extension and the CLI tool; confirm all extracted fields match. Add a second site adapter and verify it requires only one file edit.

### Implementation for User Story 2

- [x] T019 [P] [US2] Write unit tests verifying field-for-field parity between the OpenAI adapter output and the expected values captured from `backend/tests/fixtures/openai_job.html` in `backend/tests/unit/test_parse_service.py` (extend existing file)
- [x] T020 [P] [US2] Write unit tests verifying the generic adapter runs and produces non-null `title` and `role_type` for `backend/tests/fixtures/generic_job.html` in `backend/tests/unit/test_parse_service.py`
- [x] T021 [US2] Run new parity tests and confirm they pass; verify `SITE_ADAPTERS` registration pattern requires only adding one entry to `parse.py` to add a new adapter

**Checkpoint**: Adapter parity verified by tests. Single-file adapter addition confirmed.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, documentation, and cleanup across all stories.

- [x] T022 [P] Run full quality gate suite in `backend/`: `uv run pytest`, `ruff check .`, `mypy jobforce` — fix any failures
- [x] T023 [P] Verify `make check` passes from repo root (backend + frontend gates)
- [x] T024 Remove any remaining MCP Playwright step references from `.claude/skills/scout-crawl/SKILL.md` notes section
- [x] T025 [P] Update `specs/006-scout-crawl-parser/quickstart.md` with the `playwright install chromium` setup step and fixture locations for new adapter authors

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — blocks both user story phases
- **Phase 3 (US1)**: Depends on Phase 2 — CLI tool wraps the parse service
- **Phase 4 (US2)**: Depends on Phase 2 — extends parse service tests; can run in parallel with Phase 3 after Phase 2 completes
- **Phase 5 (Polish)**: Depends on Phases 3 and 4

### User Story Dependencies

- **US1**: No dependency on US2 — independently testable end-to-end
- **US2**: No dependency on US1 — tests operate on parse service directly

### Within Each Phase

- T005 (write failing tests) MUST precede T007–T012 (implementation) — test-first per Constitution Principle I
- T007 (`slug_to_location`) before T009 (OpenAI adapter uses it)
- T008 and T009 can run in parallel (different adapters, same file section — coordinate to avoid merge conflicts)
- T010 and T011 can run in parallel
- T012 depends on T008–T011

---

## Parallel Execution Examples

### Phase 2 Parallelism

```
# After T005-T006 (fixtures + failing tests):
Task A: T007 — slug_to_location helper
Task B: T008 — GENERIC_ADAPTER  (coordinate on parse.py)
# Then:
Task A: T009 — SITE_ADAPTERS (openai.com)
Task B: T010 — run_adapter()
Task C: T011 — merge()
# Then:
Task: T012 — parse_html() entry point
```

### Phase 3 + Phase 4 Parallelism (after Phase 2)

```
Stream A: T014 → T015 → T016 → T017 → T018  (US1 CLI + skill)
Stream B: T019 → T020 → T021                 (US2 parity tests)
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (`parse.py` + tests)
3. Complete Phase 3: US1 (`scout_fetch.py` + updated skill)
4. **STOP and VALIDATE**: run `/scout-crawl` against a real OpenAI URL, confirm deterministic output
5. Ship — this is the core improvement

### Incremental Delivery

1. Phase 1 + 2 → `parse.py` functional and tested
2. Phase 3 → skill is end-to-end deterministic (MVP)
3. Phase 4 → adapter parity tests locked in, extension pattern confirmed
4. Phase 5 → quality gates green, docs updated

---

## Notes

- Constitution Principle I is enforced: T005 and T014 write failing tests before any implementation
- No Anthropic SDK imported anywhere (Constitution Principle VI)
- `parse.py` functions must stay ≤ 40 lines each (Constitution Principle II) — decompose if needed
- Static HTML fixtures in `backend/tests/fixtures/` avoid live network calls in unit tests
- `scout_fetch.py` integration with a real URL is validated manually via the skill, not in automated tests (live network + headless browser is too slow/flaky for CI)
