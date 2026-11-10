# Implementation Plan: OpenAPI Specification for the Jobforce API

**Branch**: `015-openapi-api-spec` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/015-openapi-api-spec/spec.md`

## Summary

Check in a generated, deterministic `backend/openapi.yaml` built from the FastAPI app's own route declarations. Enrich every one of the 29 operations with a summary, description, parameter descriptions, typed responses and documented errors. Introduce a single `ErrorCode` catalog so every business-rule error returns `{detail, code}`; the only runtime change is the added `code` field. Describe the resume `structured_data` shape without validating it. Generate frontend TypeScript types from the spec with `openapi-typescript` and make `src/lib/types.ts` re-export them. `make check` fails on spec drift, incomplete endpoints, stale frontend types, or frontend type errors.

## Technical Context

**Language/Version**: Python 3.12 (backend); TypeScript 6 / Node 24 (frontend)

**Primary Dependencies**: FastAPI 0.141 and Pydantic 2.13 (already present; native OpenAPI 3.1 generation); pyyaml (already present). New frontend devDependency: `openapi-typescript@^7.13`.

**Storage**: N/A. No schema changes. Two new checked-in generated files: `backend/openapi.yaml` and `frontend/src/lib/api-schema.d.ts`.

**Testing**: pytest (contract tests for drift, completeness, error codes and resume permissiveness); `tsc --noEmit` plus the existing Jest suite for the frontend.

**Target Platform**: Local developer machine (macOS); localhost-only API.

**Project Type**: Web application (FastAPI backend + Next.js frontend + Chrome extension, which is untouched).

**Performance Goals**: Spec and type regeneration under 10s total (SC-006). The drift and completeness tests add under 1s to `make check`.

**Constraints**: No runtime behavior change beyond adding `code` to business-error bodies (FR-014). Existing `detail` strings stay byte-identical. Generation must work with no config, DB or network (FR-005).

**Scale/Scope**: 7 routers, 29 operations, about 35 error raise sites, 27 frontend types re-pointed, 18 importing frontend files (import paths unchanged).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Assessment | Status |
| --- | --- | --- |
| I. Test-First | Drift, completeness, error-code and resume round-trip tests are written first and fail against the current code. Existing contract tests prove FR-014 (unchanged `detail`). | ✅ |
| II. Code Quality | New modules are small (`errors.py`, `resume_schema.py`, `export_openapi.py`). The `error_responses()` helper stays under 40 lines and complexity ≤ 10. Generated files are excluded from lint. Adding `tsc --noEmit` to the gate *raises* the bar. | ✅ |
| III. Self-Improvement | This is a tooling deliverable (code generator + gate), first-class per III. `docs/retrospective.md` gets updated at the end. | ✅ |
| IV. Simplicity | Uses FastAPI's native OpenAPI hooks with no custom `openapi()` override (unless the R6 fallback is needed). One error catalog drives both runtime and docs. No generated client (YAGNI, per clarification Q1). | ✅ |
| V. Observability | Error bodies gain machine-readable codes, so skills and logs can classify failures without parsing text. Drift failures name the fix command. | ✅ |
| VI. No AI SDK | No AI involvement. The `grep -r "import anthropic" backend/` invariant is unaffected. | ✅ |

**Post-design re-check (after Phase 1)**: still ✅. The design adds 3 small backend modules and 1 frontend script, and introduces no new runtime dependencies. The R6 fallback, if triggered, adds one post-processing function; it would be logged in Complexity Tracking.

## Project Structure

### Documentation (this feature)

```text
specs/015-openapi-api-spec/
├── plan.md              # This file
├── research.md          # Phase 0: decisions R1–R9
├── data-model.md        # Phase 1: BusinessError, ErrorCode, ResumeStructuredData, enums, tags
├── quickstart.md        # Phase 1: validation walkthrough
├── contracts/
│   ├── error-codes.md   # ErrorCode catalog: status, detail, routes
│   └── tooling.md       # gen/check commands + completeness rules
└── tasks.md             # Phase 2 (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── openapi.yaml                         # NEW (generated, checked in)
├── Makefile                             # + openapi target
└── jobforce/
    ├── main.py                          # + openapi_tags, ApiError handler registration
    ├── cli/export_openapi.py            # NEW: write / --check
    ├── routers/
    │   ├── errors.py                    # NEW: ErrorCode, ApiError, BusinessError, error_responses()
    │   ├── resume_schema.py             # NEW: ResumeStructuredData + nested models, enum annotations
    │   ├── jobs.py, companies.py, forge.py, oracle.py,
    │   │   coach.py, dashboard.py, ingest.py   # summaries, param descriptions, responses=, ApiError raises
    └── services/coach.py                # ValueError → SessionNotFoundError / QuestionNotFoundError
backend/tests/contract/
    ├── test_openapi_drift.py            # NEW
    ├── test_openapi_completeness.py     # NEW
    ├── test_error_codes.py              # NEW: one request per ErrorCode → asserts {detail, code}
    └── test_forge.py                    # + permissive resume round-trip

frontend/
├── package.json                         # + openapi-typescript, gen:api, check:api, typecheck
├── eslint.config.mjs                    # ignore src/lib/api-schema.d.ts
├── scripts/check-api-types.mjs          # NEW
└── src/lib/
    ├── api-schema.d.ts                  # NEW (generated, checked in)
    └── types.ts                         # re-exports generated types; frontend-only types remain

Makefile                                 # + openapi target; frontend check gains check:api + typecheck
CLAUDE.md, DEVELOPMENT.md                # API contract pointers (FR-015)
```

**Structure Decision**: Use the existing web-app layout (`backend/`, `frontend/`). The spec lives at `backend/openapi.yaml`, beside the code it is generated from. The frontend reads it by relative path. The Chrome extension is not touched.

## Implementation Order (for /speckit-tasks)

1. **Foundation (blocks everything)**: write `errors.py` (catalog, handler, `error_responses`) and `test_error_codes.py`; the tests are red at first.
2. **US1 (P1)**: `export_openapi.py`, `make openapi`, `test_openapi_drift.py`, then the first generated `openapi.yaml`. This can merge before US2; the file is just thinner.
3. **US2 (P2)**, one router per task, parallelizable: summaries, descriptions, `Annotated` param descriptions, `responses=error_responses(...)`, `HTTPException` → `ApiError`, enum annotations. Then `resume_schema.py` with the permissive round-trip test, `openapi_tags`, and finally `test_openapi_completeness.py` going green. Regenerate the spec.
4. **US3 (P3)**: `openapi-typescript`, `gen:api` / `check:api` / `typecheck`, the `types.ts` re-export migration, fixes to frontend null-safety fallout, root Makefile wiring, and the CLAUDE.md / DEVELOPMENT.md updates.
5. **Polish**: run the quickstart end to end, update `docs/retrospective.md`, and check the skill docs that branch on `INVALID_TRANSITION` (they keep working).

## Risks

| Risk | Mitigation |
| --- | --- |
| `SkipValidation` emits serializer warnings on non-conforming resumes | The round-trip test runs with warnings as errors; use the R6 fallback |
| Generated types are stricter or more optional than the hand-written ones, so frontend compile errors appear | Expected and in scope. These are real null-safety gaps; fix them in place |
| openapi-typescript output changes between patch versions, causing a false drift failure | Pin the exact version in `package.json` (no caret) and update it deliberately via `/housekeeping` |
| A custom 422 in `responses=` suppresses FastAPI's default validation 422 | `error_responses()` always emits `anyOf[BusinessError, HTTPValidationError]` for 422; completeness rule 6 checks it |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --- | --- | --- |
| One `app.openapi` wrapper (`main.py::_register_extra_schemas`) adds the `ResumeStructuredData` components (research R6 fallback, triggered) | `SkipValidation[ResumeStructuredData]` raised Pydantic serializer warnings on non-conforming resumes (caught by `test_put_base_resume_is_permissive`). Runtime type is now `Any` with an `allOf: [$ref]` schema, so FastAPI can't discover the component itself | Typing the field as the model would validate or warn on real resumes that the skills send today (violates FR-011a/FR-014); `Any` with no schema loses the typed resume (clarification Q3) |
