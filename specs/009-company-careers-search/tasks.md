# Tasks: Company Careers Search Skill

**Input**: Design documents from `specs/009-company-careers-search/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/skill-interface.md

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add `careers_url` to the DB model and config — foundational for all stories.

- [ ] T001 Add `careers_url: Mapped[str | None]` column to `Company` in `backend/jobforce/db/models.py`
- [ ] T002 Add `careers_url: str = ""` field to `CompanyConfig` in `backend/jobforce/config.py`
- [ ] T003 Update `_seed_companies()` in `backend/jobforce/db/seed.py` to populate `careers_url` from config when set
- [ ] T004 Write SQLite migration: `ALTER TABLE companies ADD COLUMN careers_url TEXT` in `backend/jobforce/db/migrations/009_add_careers_url.sql` (run manually or via init)
- [ ] T005 [P] Add `careers_url` example to `target_companies` entries in `config/config.example.yaml`
- [ ] T006 [P] Add unit test: `CompanyConfig` accepts and round-trips `careers_url` in `backend/tests/unit/test_config.py`

**Checkpoint**: `Company` DB model has `careers_url`; config model accepts it; seed populates it.

---

## Phase 2: Foundational (Backend API — Blocks US1 write-back)

**Purpose**: `GET /api/companies` list and `PATCH /api/companies/{id}` are required by the skill to look up company IDs and write back discovered URLs.

- [ ] T007 Add `GET /api/companies` list endpoint returning `[{id, name, domain, careers_url}]` to `backend/jobforce/routers/companies.py`
- [ ] T008 Add `PATCH /api/companies/{id}` endpoint accepting `{careers_url}` and persisting it to `backend/jobforce/routers/companies.py`
- [ ] T009 [P] Add integration test: `GET /api/companies` returns seeded companies in `backend/tests/integration/test_companies_service.py`
- [ ] T010 [P] Add integration test: `PATCH /api/companies/{id}` updates `careers_url` and persists in `backend/tests/integration/test_companies_service.py`

**Checkpoint**: `cd backend && make check` passes. `GET /api/companies` and `PATCH /api/companies/{id}` work. Foundation ready for skill implementation.

---

## Phase 3: User Story 1 — Crawl All Target Companies (Priority: P1) 🎯 MVP

**Goal**: Invoking `/scout-companies` visits every company's careers page, discovers job URLs, ingests them, and prints a per-company summary.

**Independent Test**: With 2+ companies in `config.yaml`, run `/scout-companies` and confirm new job listings appear in `GET /api/jobs`.

- [ ] T011 [US1] Create `.claude/skills/scout-companies/SKILL.md` with frontmatter (`name`, `description`, `argument-hint`, `user-invocable: true`) and section stubs
- [ ] T012 [US1] Implement Step 1 in `SKILL.md`: validate backend reachable via `GET http://localhost:8000/api/jobs?limit=1`; print error and stop if not
- [ ] T013 [US1] Implement Step 2 in `SKILL.md`: load `config.yaml` via `cd backend && uv run python -c "from jobforce.config import load_config; ..."` and extract `target_companies`
- [ ] T014 [US1] Implement Step 3a in `SKILL.md`: for each company, check DB `careers_url` via `GET /api/companies`; if set, use directly
- [ ] T015 [US1] Implement Step 3b in `SKILL.md`: if no `careers_url`, probe domain paths `/careers`, `/jobs`, `/openings`, `/join-us` via Playwright MCP navigation; use first that loads
- [ ] T016 [US1] Implement Step 3e in `SKILL.md`: navigate to careers page via Playwright MCP; extract individual job listing URLs (anchor hrefs that look like job postings, not nav links)
- [ ] T017 [US1] Implement Step 3f in `SKILL.md`: after auto-discovery, call `PATCH /api/companies/{id}` with discovered `careers_url` to persist for future runs
- [ ] T018 [US1] Implement Step 3g in `SKILL.md`: for each job URL, run `cd backend && uv run python -m jobforce.cli.scout_fetch --url "<url>"` then POST result to `POST http://localhost:8000/api/ingest`
- [ ] T019 [US1] Implement Step 4 in `SKILL.md`: print per-company summary (ingested count, duplicate count, errors) and final totals matching output format in contracts/skill-interface.md
- [ ] T020 [US1] Handle edge cases in `SKILL.md`: no companies in config → fail fast; careers page not found after probing → skip and report; `scout_fetch` error for a URL → log and continue

**Checkpoint**: `/scout-companies` with no args crawls all target companies and ingests jobs. Discovered URLs are persisted. Duplicate runs skip already-ingested jobs.

---

## Phase 4: User Story 2 — Per-Company `careers_url` Override (Priority: P2)

**Goal**: Setting `careers_url` in `config.yaml` for a company causes the skill to use that URL directly without probing.

**Independent Test**: Add `careers_url: "https://boards.greenhouse.io/acme"` to a company in `config.yaml`; run `/scout-companies`; confirm it navigates to that URL without domain probing (check skill output shows the exact URL).

- [ ] T021 [US2] Update `_seed_companies()` in `backend/jobforce/db/seed.py` to upsert `careers_url` from config onto existing company rows (not just new rows)
- [ ] T022 [US2] Verify `SKILL.md` Step 3a already handles this correctly (should if T014 is done): confirm DB `careers_url` takes precedence over probing; add note in skill if logic needs clarifying

**Checkpoint**: Companies with `careers_url` in config skip domain probing entirely. Seeding updates existing rows.

---

## Phase 5: User Story 3 — Single Company Argument (Priority: P3)

**Goal**: `/scout-companies "Acme Corp"` crawls only that company.

**Independent Test**: Run `/scout-companies "Acme Corp"` with 3 companies in config; confirm only Acme Corp is crawled and reported.

- [ ] T023 [US3] Update Step 2 in `SKILL.md` to parse the optional argument; filter `target_companies` to the named company (case-insensitive); if argument provided and no match found, print "Company not found in config.yaml" and exit

**Checkpoint**: Argument filtering works. Unrecognized names exit cleanly with a clear message.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T024 [P] Run `cd backend && make check` (ruff + mypy + pytest) and fix any failures
- [ ] T025 Update `CLAUDE.md` current feature context section to reflect completed skill
- [ ] T026 [P] Manually test full flow: seed DB, start backend, run `/scout-companies` against real companies, verify jobs appear in frontend at `http://localhost:3000`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (needs `careers_url` on Company model)
- **Phase 3 (US1)**: Depends on Phase 2 (needs `GET /api/companies` + `PATCH /api/companies/{id}`)
- **Phase 4 (US2)**: Depends on Phase 1 (seed change) and Phase 3 (skill must exist)
- **Phase 5 (US3)**: Depends on Phase 3 (skill must exist — just adds argument parsing)
- **Phase 6 (Polish)**: Depends on all prior phases

### Within Phase 3

- T011 → T012 → T013 → T014 → T015 → T016 → T017 → T018 → T019 → T020 (sequential — each step builds on the previous in SKILL.md)

### Parallel Opportunities

- T005 and T006 can run in parallel with T001–T004 (different files)
- T009 and T010 can run in parallel (same file, different test functions — write sequentially or coordinate)
- T024 and T025 and T026 can run in parallel in Phase 6

---

## Implementation Strategy

### MVP (Phase 1 + 2 + 3 only)

1. Complete Phase 1: Add `careers_url` to model and config
2. Complete Phase 2: Add `GET /api/companies` + `PATCH /api/companies/{id}`
3. Complete Phase 3: Write the skill end-to-end
4. **STOP and VALIDATE**: Run `/scout-companies` against real companies
5. Ship — US2 and US3 are polish, not blockers

### Incremental Delivery

- Phase 1+2: Backend ready, skill can be tested stub-by-stub
- Phase 3: Full skill working for all companies
- Phase 4: Config override works without re-probing
- Phase 5: Single-company runs for targeted re-crawl

---

## Notes

- [P] tasks touch different files — safe to run in parallel
- Skill steps (T011–T020) are sequential within SKILL.md but the file is built incrementally
- `make check` must pass after Phase 2 before starting Phase 3
- The skill uses Playwright MCP for browser interaction — no Python browser code
- `scout_fetch` runs headless Playwright internally; ensure `uv run playwright install chromium` has been run
