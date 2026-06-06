# Tasks: Forge LaTeX & PDF Export per Job

**Input**: Design documents from `specs/013-forge-tex-pdf/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅

**Tests**: Included (Constitution Principle I — test-first, non-negotiable).

**Organization**: Tasks grouped by user story for independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Introduce the `render_template.py` CLI script and `output/` directory; no existing behaviour changes.

- [X] T001 Create `backend/jobforce/scripts/` package with `__init__.py`
- [X] T002 Add `output/` to `.gitignore` at project root

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core changes required by all user stories — `render_template.py` script, `latex_escape` filter, refactored `forge.py` service functions, and the updated export endpoint contract. Must complete before any story work begins.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T003 Write failing contract tests for updated `POST /api/resume/{id}/export` (returns `{tex_path, pdf_path}` JSON, no streaming) in `backend/tests/contract/test_forge.py`
- [X] T004 Write failing integration tests for `render_tex_cli()`, `compile_pdf_cli()`, `export_resume()`, and `_escape_latex()` in `backend/tests/integration/test_forge_service.py`
- [X] T005 [P] Implement `render_template.py` CLI script at `backend/jobforce/scripts/render_template.py` — accepts `<json_input_path> <tex_output_path>`, registers `latex_escape` Jinja2 filter, exits 0 on success / 1 on error
- [X] T006 [P] Add `latex_escape` helper function to `backend/jobforce/scripts/render_template.py` — escapes all 10 LaTeX special characters (`& % $ # _ { } ~ ^ \`) per contracts/render-template-cli.md
- [X] T007 Update `resume.tex.j2` to apply `latex_escape` filter on all string variable interpolations in `backend/jobforce/templates/resume.tex.j2`
- [X] T008 Rewrite `backend/jobforce/services/forge.py` — remove `render_pdf()` and in-process Jinja2 rendering; add `render_tex_cli(structured_data, output_dir, filename_stem) -> Path`, `compile_pdf_cli(tex_path) -> Path | None`, and `export_resume(resume, job) -> dict` per research.md Decision 6
- [X] T009 Add `_slugify(value: str) -> str` helper to `backend/jobforce/services/forge.py` — lowercases, replaces non-alphanumeric runs with `-`, strips leading/trailing `-`
- [X] T010 Add `_build_filename_stem(company: str, title: str) -> str` to `backend/jobforce/services/forge.py` — combines slugified company + title + `YYYYMMDD-HHMMSS` timestamp per FR-008
- [X] T011 Update `POST /api/resume/{id}/export` in `backend/jobforce/routers/forge.py` — remove `StreamingResponse`; call `export_resume()`; return `ExportOut(tex_path, pdf_path)` JSON per contracts/export-endpoint.md
- [X] T012 Add `ExportOut` Pydantic model to `backend/jobforce/routers/forge.py` with fields `tex_path: str` and `pdf_path: str | None`
- [X] T013 Ensure `output/` directory is auto-created in `export_resume()` using `Path.mkdir(parents=True, exist_ok=True)` in `backend/jobforce/services/forge.py`
- [X] T014 Run `make check` in `backend/` — all existing tests pass, new tests fail (red)

**Checkpoint**: Foundation ready — `render_template.py` exists, service functions implemented, endpoint returns JSON paths. New tests are red. User story work can now begin.

---

## Phase 3: User Story 1 — Skill Exports to Disk (Priority: P1) 🎯 MVP

**Goal**: The forge-tailor skill calls the export endpoint after tailoring, receives `.tex` and `.pdf` paths, and reports them to the user.

**Independent Test**: Run `/forge-tailor <job_id>` — both a `.tex` file and a PDF appear in `output/` at the reported paths; skill prints both paths clearly.

- [X] T015 [US1] Update Step 6 of `.claude/skills/forge-tailor/SKILL.md` — replace blob-save logic with: call `POST /api/resume/<id>/export`, read `tex_path`/`pdf_path` from JSON response, print both paths; print LaTeX-unavailable note when `pdf_path` is null, per plan.md skill detail section
- [X] T016 [US1] Verify skill integration end-to-end: run `make check` in `backend/` — contract and integration tests for the export endpoint now pass (green)

**Checkpoint**: User Story 1 complete — skill exports files to disk and reports paths. Backend tests green.

---

## Phase 4: User Story 2 — Forge UI Export (Priority: P2)

**Goal**: The Forge web UI provides an Export button that writes files to disk and displays the returned paths (no browser download).

**Independent Test**: Click "Export" on a tailored resume in the Forge UI — a panel appears showing the `.tex` path and `.pdf` path (or LaTeX-unavailable note). Files exist on disk at those paths.

- [X] T017 [P] [US2] Write failing frontend test for `ExportButton` component in `frontend/src/components/forge/ExportButton.test.tsx` — asserts it displays `tex_path` and `pdf_path` from a mocked API response
- [X] T018 [P] [US2] Update `exportResume()` in `frontend/src/lib/api.ts` — rename from `exportResumePdf()`; change return type from `Blob` to `{ tex_path: string; pdf_path: string | null }`
- [X] T019 [P] [US2] Update `ExportResponse` type in `frontend/src/lib/types.ts` — add `tex_path: string` and `pdf_path: string | null` fields; remove blob-related types if any
- [X] T020 [US2] Create `frontend/src/components/forge/ExportButton.tsx` — replaces `PDFDownloadButton.tsx`; calls `exportResume(resumeId)`, displays `tex_path` and `pdf_path` as read-only text; shows LaTeX-unavailable note when `pdf_path` is null; handles loading and error states (depends on T018, T019)
- [X] T021 [US2] Update `frontend/src/app/forge/page.tsx` — replace `<PDFDownloadButton>` with `<ExportButton>`; show export result panel below the diff (depends on T020)
- [X] T022 [US2] Delete `frontend/src/components/forge/PDFDownloadButton.tsx` — component replaced by `ExportButton.tsx`
- [X] T023 [US2] Run `npm run lint` and `npm test` in `frontend/` — all tests pass

**Checkpoint**: User Story 2 complete — Forge UI exports to disk and shows file paths. Frontend tests green.

---

## Phase 5: User Story 3 — Meaningful Filenames (Priority: P3)

**Goal**: Exported filenames include company name, job title, and timestamp — guaranteed unique and human-readable.

**Independent Test**: Export resumes for two different jobs; confirm filenames are distinct, include the company and title, and follow the pattern `resume-<company>-<title>-<YYYYMMDD-HHMMSS>.tex/.pdf`.

- [X] T024 [US3] Write failing unit tests for `_slugify()` and `_build_filename_stem()` in `backend/tests/integration/test_forge_service.py` — cover: special chars, unicode, long names, collision avoidance via timestamp
- [X] T025 [US3] Verify `_slugify()` and `_build_filename_stem()` implementations (added in T009/T010) pass all unit tests — run `make check` in `backend/`

**Checkpoint**: All three user stories complete. Filenames are meaningful and unique.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Cleanup, logging, gitignore, and final validation across all stories.

- [X] T026 [P] Add structured logging to `render_tex_cli()` and `compile_pdf_cli()` in `backend/jobforce/services/forge.py` — log start, success with path, and failure with reason
- [X] T027 [P] Remove unused `latex_source` and `pdf_path` columns from `Resume` model display if they cause confusion — verify they remain in DB schema unchanged (no migration needed; just audit references)
- [X] T028 [P] Verify `output/` is listed in `.gitignore` at project root (T002 — confirm done)
- [X] T029 Run full `make check` in `backend/` — zero ruff warnings, zero mypy errors, 100% test pass rate, no coverage regression
- [X] T030 Run `npm run lint` and `npm test` in `frontend/` — zero ESLint errors, all tests pass
- [X] T031 Verify `grep -r "import anthropic" backend/` returns zero results (Constitution VI gate)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **blocks all user stories**
- **Phase 3 (US1 - Skill)**: Depends on Phase 2
- **Phase 4 (US2 - UI)**: Depends on Phase 2; independent of Phase 3
- **Phase 5 (US3 - Filenames)**: Depends on Phase 2 (T009/T010 implemented there); verifies in this phase
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5

### User Story Dependencies

- **US1 (Skill)**: Independent — only requires Foundational phase
- **US2 (Forge UI)**: Independent — only requires Foundational phase; can run in parallel with US1
- **US3 (Filenames)**: Core implementation in Foundational (T009/T010); Phase 5 adds tests and verifies

### Within Each Phase

- Tests written and confirmed failing **before** implementation (Constitution I)
- Models/helpers before services; services before endpoints; endpoints before UI
- `make check` run after each phase checkpoint

### Parallel Opportunities

- T005 and T006 can run in parallel (same file, but both are additive — sequence T005 then T006)
- T017, T018, T019 (frontend — different files) can run in parallel
- T026, T027, T028 (polish — different files) can run in parallel
- US1 (Phase 3) and US2 (Phase 4) can run in parallel once Phase 2 is complete

---

## Parallel Example: Phase 4 (User Story 2)

```text
# These three tasks touch different files — launch in parallel:
T017: Write ExportButton test in frontend/src/components/forge/ExportButton.test.tsx
T018: Update exportResume() in frontend/src/lib/api.ts
T019: Update ExportResponse type in frontend/src/lib/types.ts

# Then sequentially (depend on T018, T019):
T020: Implement ExportButton.tsx
T021: Wire ExportButton into forge/page.tsx
T022: Delete PDFDownloadButton.tsx
T023: npm run lint && npm test
```

---

## Implementation Strategy

### MVP (User Story 1 Only)

1. Complete Phase 1: Setup (T001–T002)
2. Complete Phase 2: Foundational (T003–T014) — red tests, then green
3. Complete Phase 3: User Story 1 (T015–T016)
4. **STOP and VALIDATE**: Run `/forge-tailor` against a real job; confirm `.tex` and `.pdf` in `output/`

### Incremental Delivery

1. Setup + Foundational → backend working, tests green
2. US1 (Skill) → CLI workflow complete → validate with real run
3. US2 (Forge UI) → UI workflow complete → validate in browser
4. US3 (Filenames) → already implemented in Foundational; Phase 5 adds test coverage
5. Polish → clean slate

---

## Notes

- [P] = different files, no dependencies within phase
- Tests must be written **and confirmed failing** before implementation (Constitution I)
- `make check` must pass at each checkpoint before advancing
- `output/` is gitignored — never commit generated files
- `503 LATEX_UNAVAILABLE` response code is retired; use `pdf_path: null` instead
- `PDFDownloadButton.tsx` is deleted in T022 — do not leave dead code
