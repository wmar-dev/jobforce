---
description: "Task list for Jobforce — Superhero Job Hunt Command Center"
---

# Tasks: Jobforce — Superhero Job Hunt Command Center

**Input**: Design documents from `specs/001-job-force-app/`

**Prerequisites**: plan.md ✅ | spec.md ✅ | data-model.md ✅ | contracts/ ✅ | research.md ✅

**Tests**: Test tasks are included per the constitution's Test-First principle (NON-NEGOTIABLE). Tests must be written and confirmed failing before implementation.

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story?] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1–US5)
- Exact file paths included in all descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Repository layout, tooling, and configuration before any feature work begins.

- [x] T001 Create root directory structure: `backend/`, `frontend/`, `chrome-extension/`, `.claude/skills/` per plan.md
- [x] T002 [P] Create `backend/pyproject.toml` with dependencies: fastapi, sqlalchemy[asyncio], aiosqlite, pydantic-settings[yaml], jinja2, anthropic, ruff, mypy, pytest, pytest-asyncio, pytest-cov
- [x] T003 [P] Create `frontend/package.json` with dependencies: next@14, react@18, typescript, tailwindcss, shadcn/ui, swr; add `dev` script running both servers via concurrently
- [x] T004 [P] Create root `Makefile` with targets: `dev` (start backend + frontend), `check` (run all quality gates), `seed` (run backend seed script)
- [x] T005 [P] Create `backend/Makefile` with `check` target: ruff lint + mypy type-check + pytest with coverage
- [x] T006 [P] Create `config.example.yaml` documenting all required and optional fields: database.path, search.queries[], search.target_companies[], user.full_name, user.skills[]
- [x] T007 [P] Create `.gitignore` additions: `backend/data/jobforce.db`, `backend/data/pages/`, `frontend/.next/`, `chrome-extension/icons/*.png` (placeholders)
- [x] T008 [P] Create `frontend/next.config.ts` with API proxy rewrites: `/api/*` → `http://localhost:8000/api/*` in development
- [x] T009 [P] Create `frontend/tailwind.config.ts` with shadcn/ui preset and superhero color theme tokens

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend infrastructure all user stories depend on. No story work begins until this phase is complete.

**⚠️ CRITICAL**: Phases 3–7 cannot start until this phase is complete.

- [x] T010 Create `backend/jobforce/config.py`: pydantic-settings YAML loader for `config.yaml`; models for `DatabaseConfig`, `SearchConfig`, `CompanyConfig`, `UserConfig`; fail-fast validation on startup
- [x] T011 Create `backend/jobforce/db/engine.py`: async SQLAlchemy engine with aiosqlite driver, WAL mode enabled (`PRAGMA journal_mode=WAL`), pool_size=5, max_overflow=10
- [x] T012 Create `backend/jobforce/db/models.py`: all 8 ORM models — `Company`, `JobListing`, `StatusTransition`, `PageSnapshot`, `Resume`, `InterviewSession`, `MeetingNote`, `UserProfile`, `SearchConfig` — with relationships, CHECK constraints, and indexes per data-model.md
- [x] T013 Create `backend/jobforce/db/init.py`: `create_all()` async function creating tables and indexes; idempotent (safe to re-run)
- [x] T014 Create `backend/jobforce/db/seed.py`: `seed_from_config()` idempotent async function seeding `Company` and `SearchConfig` rows from `config.yaml`; skips existing records
- [x] T015 Create `backend/jobforce/main.py`: FastAPI app factory with lifespan (DB init + seed on startup), CORSMiddleware (localhost origins), structured request logging middleware, router registration stubs
- [x] T016 Create `backend/tests/conftest.py`: async pytest fixtures — `test_client` (AsyncClient with temp SQLite DB), `db_session`, `sample_company`, `sample_job` factories
- [x] T017 [P] Create `backend/tests/unit/test_config.py`: unit tests for config loader — valid YAML passes, missing required fields raise ValidationError, extra fields are ignored
- [x] T018 [P] Create `backend/tests/unit/test_db_models.py`: unit tests for ORM model constraints — status CHECK constraint rejects invalid values, `fit_scored` defaults to 0, status transitions append-only
- [x] T019 Create `frontend/src/lib/types.ts`: TypeScript interfaces for all API response shapes per contracts/api-contracts.md — `JobListing`, `Company`, `Resume`, `InterviewSession`, `MeetingNote`, `DashboardSummary`, `OracleRankResult`
- [x] T020 Create `frontend/src/lib/api.ts`: typed fetch helper functions for all API endpoints; handles errors, returns typed responses; base URL from env var with localhost:8000 fallback
- [x] T021 Create `frontend/src/app/layout.tsx`: root layout with `Sidebar` navigation component (hero nav: HQ | Scout | Oracle | Forge | Coach)
- [x] T022 Create `frontend/src/components/layout/Sidebar.tsx`: sidebar with superhero-themed navigation links, `HeroCard` identity chips per agent, active route highlighting
- [x] T023 Create `frontend/src/components/layout/HeroCard.tsx`: agent identity card component showing hero name, codename, power description, and themed color/icon

**Checkpoint**: Backend starts (`uvicorn jobforce.main:app`), DB creates tables, frontend builds, sidebar renders. Quality gates pass: `make check`.

---

## Phase 3: User Story 1 — Scout: Find & Ingest Job Listings (Priority: P1) 🎯 MVP

**Goal**: User can capture a job listing via Chrome extension or Playwright MCP skill, have it stored with its raw HTML snapshot, and view it in the Scout job board.

**Independent Test**: Load the Chrome extension, navigate to any job listing URL, click the extension button, and verify the listing appears in the Scout job board at `/jobs`.

### Tests for User Story 1 (Write first — confirm failing before implementing)

- [ ] T024 [P] [US1] Write contract test `backend/tests/contract/test_ingest.py`: POST /api/ingest with valid payload returns 201 with job id; duplicate URL returns 409; missing source_url returns 422
- [ ] T025 [P] [US1] Write contract test `backend/tests/contract/test_jobs.py`: GET /api/jobs returns paginated list; filter by status/location/role-type returns correct subset; GET /api/jobs/{id} returns full detail with status_history
- [ ] T026 [P] [US1] Write integration test `backend/tests/integration/test_scout_service.py`: dedup by URL works; HTML >500KB routes to file, ≤500KB stored as BLOB; company auto-created from company_name
- [ ] T027 [P] [US1] Write integration test `backend/tests/integration/test_storage_service.py`: BLOB threshold routing; `verify_integrity()` detects missing file_path on disk
- [ ] T027a [US1] **Red-gate checkpoint**: run `pytest backend/tests/contract/test_ingest.py backend/tests/contract/test_jobs.py backend/tests/integration/test_scout_service.py backend/tests/integration/test_storage_service.py` — confirm ALL tests fail (not error) before proceeding to implementation

### Implementation for User Story 1

- [ ] T028 [US1] Create `backend/jobforce/services/storage.py`: BLOB vs file routing logic (threshold 500KB), `store_snapshot()`, `retrieve_snapshot()`, `verify_integrity()` check
- [ ] T029 [US1] Create `backend/jobforce/services/scout.py`: `ingest_listing()` — dedup by source_url, auto-create Company from company_name, create JobListing, call storage service for HTML snapshot, record initial StatusTransition (saved)
- [ ] T030 [US1] Create `backend/jobforce/routers/ingest.py`: POST /api/ingest endpoint; validates request, calls scout service, returns 201 or 409
- [ ] T031 [US1] Create `backend/jobforce/routers/jobs.py`: GET /api/jobs (paginated, filterable by status/company_id/min_score); GET /api/jobs/{id} (full detail + status_history); PATCH /api/jobs/{id}/status (validate transition, append StatusTransition)
- [ ] T032 [US1] Create `chrome-extension/manifest.json`: MV3 manifest with permissions (activeTab, storage, scripting), host_permissions (localhost:8000), background service_worker, content_scripts
- [ ] T033 [US1] Create `chrome-extension/content.js`: extract source_url, title, company_name, location, description, outerHTML from DOM; send to background service worker via chrome.runtime.sendMessage
- [ ] T034 [US1] Create `chrome-extension/background.js`: receive message from content script; POST to /api/ingest; show badge (✅ Saved / ❌ Server not running); persist last_ingested_url in chrome.storage.local
- [ ] T035 [US1] Create `chrome-extension/popup.html` and `chrome-extension/popup.js`: simple popup showing backend status (running/not running) and last captured URL
- [ ] T036 [P] [US1] Create `chrome-extension/tests/test_content_extraction.js`: manual test script asserting content.js extracts expected fields from a sample HTML fixture
- [ ] T037 [US1] Create `frontend/src/app/jobs/page.tsx`: Scout job board page — fetches jobs via useJobs hook, renders JobTable with status filter tabs (All / Saved / Applied / Interviewing / Offer / Rejected / Withdrawn) and secondary filter controls for location and role type
- [ ] T037a [P] [US1] Add `location` and `role_type` query params to `GET /api/jobs` in `backend/jobforce/routers/jobs.py`; filter applied in SQLAlchemy WHERE clause (partial match for location, exact match for role_type)
- [ ] T038 [P] [US1] Create `frontend/src/components/jobs/JobTable.tsx`: sortable table of job listings showing title, company, location, status badge, fit score (if scored), crawled date
- [ ] T039 [P] [US1] Create `frontend/src/components/jobs/StatusBadge.tsx`: colour-coded badge for all 6 pipeline statuses (saved=grey, applied=blue, interviewing=yellow, offer=green, rejected=red, withdrawn=purple)
- [ ] T040 [P] [US1] Create `frontend/src/hooks/useJobs.ts`: SWR hook for GET /api/jobs with status/company/location/role_type filter params
- [ ] T041 [US1] Create `.claude/skills/speckit-scout-crawl.md`: Playwright MCP skill — navigate to URL, extract text content, call POST /api/ingest; handle auth-required sites with manual login prompt

**Checkpoint**: Chrome extension captures a real job listing, it appears in the Scout job board. `make check` passes.

---

## Phase 4: User Story 2 — Oracle: Rank Jobs by Fit (Priority: P2)

**Goal**: User can run Oracle to score all saved jobs against their profile, see ranked results with confidence indicators, and get a warning when a job description is too sparse to score reliably.

**Independent Test**: Create a user profile, run Oracle ranking on 3+ saved listings, verify results are ordered by score with rationale and confidence level per result.

### Tests for User Story 2

- [ ] T042 [P] [US2] Write contract test `backend/tests/contract/test_oracle.py`: POST /api/oracle/rank returns ranked array with score, confidence, rationale; GET /api/oracle/rank/{id} returns cached result; sparse description returns low confidence + warning field
- [ ] T043 [P] [US2] Write contract test extension in `backend/tests/contract/test_jobs.py`: PATCH /api/jobs/{id}/status validates transitions; rejected/withdrawn/offer statuses excluded from Oracle ranking by default
- [ ] T043a [US2] **Red-gate checkpoint**: run `pytest backend/tests/contract/test_oracle.py` — confirm ALL tests fail before proceeding to implementation

### Implementation for User Story 2

- [ ] T044 [US2] Create `backend/jobforce/services/oracle.py`: `rank_jobs()` — fetch user profile + job descriptions, build Anthropic SDK prompt for scoring, parse score (0.0–1.0) + confidence (high/medium/low) + rationale + optional warning; set `fit_scored=1`, `fit_score`, `fit_confidence` on JobListing
- [ ] T045 [US2] Create `backend/jobforce/routers/oracle.py`: POST /api/oracle/rank (accepts optional job_ids, defaults to all active); GET /api/oracle/rank/{job_id} (cached result)
- [ ] T046 [US2] Create `backend/jobforce/routers/profile.py`: GET /api/profile; PUT /api/profile (upsert single-row UserProfile)
- [ ] T047 [P] [US2] Create `frontend/src/app/oracle/page.tsx`: Oracle ranking view — run ranking button, ranked job list ordered by fit_score, confidence badge per result, sparse-description warning callout
- [ ] T048 [P] [US2] Create `frontend/src/hooks/useProfile.ts`: SWR hook for GET/PUT /api/profile
- [ ] T049 [US2] Create `.claude/skills/speckit-oracle-rank.md`: Oracle Claude Code skill — fetch profile, fetch saved jobs, POST /api/oracle/rank, print ranked results to terminal

**Checkpoint**: Running Oracle on 3 jobs returns scored, ordered results with confidence indicators. `make check` passes.

---

## Phase 5: User Story 5 — HQ Dashboard & Meeting Notes (Priority: P2)

**Goal**: User opens HQ Dashboard and sees pipeline counts, recent activity, and can log meeting notes per company with in-app status updates.

**Note**: US5 is co-priority P2 with Oracle. It can be developed in parallel with Phase 4 by a second developer since it shares no implementation files.

**Independent Test**: Create 5 job listings across different statuses, add a meeting note to one company, open HQ Dashboard and verify counts match and meeting note appears in activity feed.

### Tests for User Story 5

- [ ] T050 [P] [US5] Write contract test `backend/tests/contract/test_dashboard.py`: GET /api/dashboard returns correct counts per status including withdrawn; recent_transitions and recent_notes present
- [ ] T051 [P] [US5] Write contract test for companies in `backend/tests/contract/test_dashboard.py`: POST /api/companies/{id}/notes creates note; GET /api/companies/{id}/notes returns reverse-chron; GET /api/companies/{id} returns embedded listings + notes
- [ ] T051a [US5] **Red-gate checkpoint**: run `pytest backend/tests/contract/test_dashboard.py` — confirm ALL tests fail before proceeding to implementation

### Implementation for User Story 5

- [ ] T052 [US5] Create `backend/jobforce/routers/dashboard.py`: GET /api/dashboard — aggregate pipeline counts (all 6 statuses), last 10 status transitions, last 5 meeting notes
- [ ] T053 [US5] Create `backend/jobforce/routers/companies.py`: GET /api/companies/{id} (company detail with listings + notes); POST /api/companies/{id}/notes; GET /api/companies/{id}/notes (reverse-chron)
- [ ] T054 [P] [US5] Create `frontend/src/app/page.tsx`: HQ Dashboard — PipelineSummary widget, ActivityFeed widget, quick-access HeroCard links to each agent section
- [ ] T055 [P] [US5] Create `frontend/src/components/dashboard/PipelineSummary.tsx`: pipeline count cards for all 6 statuses with colour coding matching StatusBadge
- [ ] T056 [P] [US5] Create `frontend/src/components/dashboard/ActivityFeed.tsx`: chronological feed of recent status transitions and meeting notes with timestamps
- [ ] T057 [P] [US5] Create `frontend/src/app/companies/[id]/page.tsx`: company detail view — all listings with StatusTransitionModal, meeting notes list in reverse-chron order, add-note form
- [ ] T058 [P] [US5] Create `frontend/src/components/jobs/StatusTransitionModal.tsx`: modal for advancing/changing pipeline status inline; lists valid transitions for current status; blocks invalid transitions
- [ ] T059 [P] [US5] Create `frontend/src/hooks/useDashboard.ts`: SWR hook for GET /api/dashboard with auto-refresh interval

**Checkpoint**: HQ Dashboard loads with accurate pipeline counts. Status transitions work in-app. Meeting notes save and appear in feed. `make check` passes.

---

## Phase 6: User Story 3 — Forge: Tailor Resume & Generate PDF (Priority: P3)

**Goal**: User provides a base resume as structured data, selects a target job, Forge tailors the content, and renders a downloadable PDF via LaTeX.

**Independent Test**: Upload a base resume, select a saved job, run Forge tailoring, verify a PDF is generated and downloadable with content referencing keywords from the job description.

### Tests for User Story 3

- [ ] T060 [P] [US3] Write contract test `backend/tests/contract/test_forge.py`: GET /api/resume/base returns base resume; PUT /api/resume/base saves it; POST /api/resume/tailor returns tailored variant; POST /api/resume/{id}/export returns PDF bytes (200) or 503 if LaTeX unavailable
- [ ] T061 [P] [US3] Write integration test `backend/tests/integration/test_forge_service.py`: tailored resume contains keywords from job description; original content not fabricated; LaTeX renders without subprocess error on CI
- [ ] T061a [US3] **Red-gate checkpoint**: run `pytest backend/tests/contract/test_forge.py backend/tests/integration/test_forge_service.py` — confirm ALL tests fail before proceeding to implementation

### Implementation for User Story 3

- [ ] T062 [US3] Create `backend/jobforce/templates/resume.tex.j2`: Jinja2 LaTeX resume template with `\VAR{}` delimiters for personal_info, work_history[], education[], skills[]; professional typesetting with section headings
- [ ] T063 [US3] Create `backend/jobforce/services/forge.py`: `tailor_resume()` — use Anthropic SDK to adjust emphasis/keywords against job description without fabricating content; `compute_diff()` — field-level diff between base and tailored `structured_data` returning list of `{field, original, tailored}` objects; `render_pdf()` — Jinja2 render to .tex, latexmk subprocess, stream PDF bytes, cleanup temp files in try/finally
- [ ] T064 [US3] Create `backend/jobforce/routers/forge.py`: GET /api/resume/base; PUT /api/resume/base; POST /api/resume/tailor (response includes `diff` array from `compute_diff()`); POST /api/resume/{id}/export (StreamingResponse for PDF)
- [ ] T065 [P] [US3] Create `frontend/src/app/forge/page.tsx`: Forge page — base resume structured data editor, target job selector, diff view (ResumeDiff), generate PDF button with loading state
- [ ] T066 [P] [US3] Create `frontend/src/components/forge/ResumeDiff.tsx`: side-by-side comparison of original vs tailored content driven by backend `diff` array; highlights added/removed text per field
- [ ] T067 [P] [US3] Create `frontend/src/components/forge/PDFDownloadButton.tsx`: button triggering POST /api/resume/{id}/export, handles loading/error/503 (LaTeX not available) states
- [ ] T068 [US3] Create `.claude/skills/speckit-forge-tailor.md`: Forge Claude Code skill — accept job_id arg, fetch base resume, POST /api/resume/tailor, POST export, save PDF to local path, print path

**Checkpoint**: Forge produces a tailored PDF resume for a saved job listing. `make check` passes.

---

## Phase 7: User Story 4 — Coach: Interview Preparation (Priority: P4)

**Goal**: User selects a target job, Coach scours the web for real interview questions, recommends LeetCode problems and system design questions, and runs a mock interview with per-answer feedback.

**Independent Test**: Select a saved job, run Coach prep, verify results include web-sourced questions with URLs, LeetCode recommendations for technical roles, and all 4 question categories (behavioral, coding, system_design, role_specific).

### Tests for User Story 4

- [ ] T069 [P] [US4] Write contract test `backend/tests/contract/test_coach.py`: POST /api/coach/prep returns session with questions across all 4 categories; at least one coding question has leetcode_url; POST /api/coach/sessions/{id}/answer returns feedback + score; GET /api/coach/sessions/{id}/summary returns overall_score + areas_to_improve
- [ ] T070 [P] [US4] Write unit test `backend/tests/unit/test_db_models.py` addition: InterviewSession question JSON schema validates required fields (id, category, text)
- [ ] T070a [US4] **Red-gate checkpoint**: run `pytest backend/tests/contract/test_coach.py` — confirm ALL tests fail before proceeding to implementation

### Implementation for User Story 4

- [ ] T071 [US4] Create `backend/jobforce/services/coach.py`: `generate_prep_pack()` — use Playwright MCP (or Anthropic web search tool) to search Glassdoor/Blind for company interview questions; search LeetCode for role-relevant problems; use Anthropic SDK to synthesise into categorised question pack (behavioral/coding/system_design/role_specific) with source attribution; `evaluate_answer()` — score response + generate feedback
- [ ] T072 [US4] Create `backend/jobforce/routers/coach.py`: POST /api/coach/prep; POST /api/coach/sessions/{id}/answer; GET /api/coach/sessions/{id}/summary
- [ ] T073 [P] [US4] Create `frontend/src/app/coach/page.tsx`: Coach page — target job selector, interview prep pack display with category tabs, mock interview mode toggle
- [ ] T074 [P] [US4] Create `frontend/src/components/coach/QuestionCard.tsx`: displays question text, category badge, source URL link, LeetCode link (if present), guidance section; expandable answer framework
- [ ] T075 [P] [US4] Create `frontend/src/components/coach/MockInterviewPanel.tsx`: sequential question-answer interface; text area for user response; submit for feedback; shows Coach feedback inline; session summary at end
- [ ] T076 [US4] Create `.claude/skills/speckit-coach-prep.md`: Coach Claude Code skill — accept job_id, invoke Playwright MCP for web search, POST /api/coach/prep, print categorised question pack with LeetCode links to terminal

**Checkpoint**: Coach delivers a web-sourced prep pack with LeetCode links and system design questions. Mock interview session produces per-answer feedback and a summary. `make check` passes.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Quality, observability, and self-improvement artifacts across all stories.

- [ ] T077 [P] Add timing instrumentation middleware to `backend/jobforce/main.py`: log request duration for all /api/oracle, /api/forge, /api/coach endpoints; log Anthropic SDK token usage per call
- [ ] T077a [P] Add performance assertion test to `backend/tests/contract/test_forge.py`: POST /api/resume/{id}/export with a pre-rendered .tex fixture must complete in ≤30 seconds (SC-008); use `time.monotonic()` around the request; skip if LaTeX not installed (`pytest.mark.skipif`)
- [ ] T078 [P] Add `backend/jobforce/routers/jobs.py` PATCH validation: enforce valid state machine transitions (saved→applied→interviewing→offer; any→rejected/withdrawn; offer/rejected/withdrawn terminal) with 422 on invalid
- [ ] T079 [P] Create `docs/retrospective.md`: structured feedback template per constitution §III — sections for what worked, what to improve, recurring failure patterns; commit as empty template
- [ ] T080 [P] Update `backend/jobforce/db/models.py`: add `storage.verify_integrity()` call to FastAPI startup lifespan to cross-reference all `file_path` references against filesystem
- [ ] T081 [P] Create `frontend/src/components/jobs/StatusTransitionModal.tsx` guard: disable transitions to terminal states (offer/rejected/withdrawn already in terminal); surface confirmation dialog for destructive transitions (rejected/withdrawn)
- [ ] T082 [P] Run `make check` across all three projects (backend, frontend, chrome-extension manual test); fix all ruff, mypy, and Jest failures to zero
- [ ] T083 [P] Validate `quickstart.md` end-to-end: follow all steps from Prerequisites through "Run the Hero Agents"; fix any step that fails or is missing

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately; all T001–T009 are parallelisable
- **Phase 2 (Foundational)**: Requires Phase 1 complete — blocks all user story phases
- **Phase 3 (Scout/US1)**: Requires Phase 2 — first user story, delivers MVP
- **Phase 4 (Oracle/US2)**: Requires Phase 2 + user profile endpoint from Phase 3
- **Phase 5 (HQ Dashboard/US5)**: Requires Phase 2 — **can run in parallel with Phase 4**
- **Phase 6 (Forge/US3)**: Requires Phase 2 + JobListing entity from Phase 3
- **Phase 7 (Coach/US4)**: Requires Phase 2 + JobListing entity from Phase 3
- **Phase 8 (Polish)**: Requires all story phases complete

### User Story Dependencies

- **US1 (Scout)**: Foundational only — no story dependencies
- **US2 (Oracle)**: Needs US1 for job listings to rank; needs profile endpoint (T046)
- **US5 (HQ Dashboard)**: Needs US1 for job listings; independent of US2/US3/US4
- **US3 (Forge)**: Needs US1 for job listings to target; independent of US2/US5
- **US4 (Coach)**: Needs US1 for job listings to target; independent of US2/US3/US5

### Within Each User Story

1. Contract tests written first → confirmed failing
2. Services implemented → tests pass
3. Routers implemented → contract tests pass
4. Frontend components implemented
5. Claude Code skill created
6. `make check` passes → story complete

### Parallel Opportunities

**Phase 1**: T002, T003, T004, T005, T006, T007, T008, T009 all run in parallel (different files).

**Phase 2**: T010→T011→T012 are sequential (engine before models); T017, T018 run parallel after T012; T019–T023 (frontend foundation) run in parallel with T010–T018.

**Phase 3**: T024–T027 (tests, write first); T028→T029→T030 sequential (storage→scout→router); T031 parallel with T030; T032–T036 (Chrome extension) parallel with backend; T037–T040 (frontend) parallel with backend.

**Phases 4 & 5**: Can run fully in parallel (zero shared files).

---

## Implementation Strategy

### MVP (User Story 1 only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: Scout (US1)
4. **STOP and VALIDATE**: Capture a real job listing with the Chrome extension; verify it appears at `/jobs`
5. Demo-ready MVP

### Incremental Delivery

1. Setup + Foundational → base app running
2. Scout (US1) → job capture works → **MVP demo**
3. Oracle (US2) + HQ Dashboard (US5) in parallel → ranking + overview work
4. Forge (US3) → resume PDF works
5. Coach (US4) → interview prep works
6. Polish → production-quality

### Parallel Team Strategy (3 developers)

- **Dev A**: Phase 3 (Scout + Chrome extension)
- **Dev B**: Phase 4 (Oracle) then Phase 6 (Forge)
- **Dev C**: Phase 5 (HQ Dashboard) then Phase 7 (Coach)
- All share Phase 1 + Phase 2 completion as gate

---

## Notes

- `[P]` = different files, no in-flight dependencies — safe to parallelise
- `[USn]` maps to User Story n in spec.md for full traceability
- Constitution gate: write tests first, confirm failing, then implement (NON-NEGOTIABLE)
- Run `make check` after each story phase before moving to next
- Commit after each completed task or logical group
- Backend `data/` directory is gitignored — create it locally on first run
- LaTeX (`latexmk`) must be installed before Phase 6 tasks can be validated end-to-end
