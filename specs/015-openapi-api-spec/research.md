# Research: OpenAPI Specification for the Jobforce API

**Feature**: 015-openapi-api-spec | **Date**: 2026-11-09

## Baseline (measured)

- FastAPI 0.141.1, Pydantic 2.13.5. `create_app().openapi()` already produces an OpenAPI **3.1.0** document: 22 paths, **29 operations**, 39 component schemas.
- `create_app()` does **not** read config or touch the DB (that happens in `lifespan`), so the document can be produced offline with no `config.yaml` (satisfies FR-005).
- All operations already have a tag (`scout`, `jobs`, `oracle`, `forge`, `coach`, `dashboard`, `companies`); no `openapi_tags` descriptions exist. No operation has a `summary`; descriptions come only from docstrings where present.
- 4 operations declare no `response_model`. `POST /jobs/bulk-archive` gets an inferred schema from its `-> dict[str, int]` return annotation; `POST /oracle/rank` returns a 501 `JSONResponse` and documents a bogus 200.
- Errors: ~35 raise sites. All use `HTTPException(detail=str)` except `PATCH /jobs/{id}/status`, which returns `{"detail", "code": "INVALID_TRANSITION"}`. None of these appear in the generated document.
- `ResumeOut.structured_data` and `TailorRequest.structured_data` are `Any`. `PUT /resume/base` accepts any JSON body.
- Enum-like fields (`status`, `role_type`, `fit_confidence`, `category`) are typed `str`. The frontend hand-writes literal unions for them.
- Frontend: `src/lib/types.ts` (213 lines, 27 exported types) is imported by 18 files. `npm run lint` is **only** ESLint; `tsc --noEmit` passes today but is **not** in `make check`.

---

## R1. How the spec file is produced

**Decision**: A backend CLI module `jobforce/cli/export_openapi.py` builds the document from `create_app().openapi()` and writes `backend/openapi.yaml`. `--check` mode compares instead of writing. Wired as `make openapi` (writes) in `backend/Makefile`.

**Rationale**: FastAPI already introspects the routes, so the spec is derived from code (FR-002). A CLI module matches the existing `jobforce/cli/*` pattern. No server, DB or network is needed (FR-005).

**Alternatives considered**:
- *Fetch `/openapi.json` from a running server*: needs a server, so it violates FR-005.
- *Hand-written design-first YAML*: violates FR-002, and the API already exists.

## R2. File format and determinism

**Decision**: YAML via the already-installed `pyyaml` (`safe_dump(sort_keys=False, allow_unicode=True, width=100)`), with a trailing newline. Keep FastAPI's insertion order (routers in registration order, then route order), which is stable. Don't add a `servers` block, so nothing depends on the machine.

**Rationale**: YAML is easier to read and diff for a human reviewer than single-line JSON, and `openapi-typescript` reads it natively. Insertion order mirrors the code layout. `sort_keys=True` would scatter related keys (`summary` after `responses`).

**Alternatives considered**: JSON with `indent=2`. Equally deterministic, but noisier diffs (quotes, braces) and harder to scan. Rejected on readability, a close call.

## R3. Drift and completeness enforcement

**Decision**: Two pytest modules under `backend/tests/contract/`, which run automatically inside the existing `make check`:
1. `test_openapi_drift.py`: regenerates in memory and asserts equality with `backend/openapi.yaml`. On failure the message reads: `openapi.yaml is out of date — run: cd backend && make openapi`.
2. `test_openapi_completeness.py`: walks every operation and asserts it has a summary, a description, tags, a non-empty 2xx schema (or a 204 with no content), descriptions on every path and query parameter, and a business-error response when the route can raise one. It also checks that every tag has an `openapi_tags` description. Failures name `METHOD /path` and the missing item.

**Rationale**: Pytest is the existing gate and is test-first friendly (Constitution I). It needs no new Make wiring and runs in well under a second.

**Alternatives considered**: A separate `make openapi-check` target. Developers would have to remember it, and it's redundant with pytest.

## R4. Documenting routes

**Decision**: Use FastAPI's native hooks only:
- `summary=` on each route decorator, and the docstring as the description.
- `Query(description=...)` / `Path(description=...)` via `Annotated` on every parameter.
- `responses=error_responses(ErrorCode.JOB_NOT_FOUND, ...)` on each route. The helper builds the `responses` dict from the error catalog (R5).
- `openapi_tags=[...]` passed to `FastAPI(...)` with a one-line description per tag. Keep the existing tag names (`scout` covers the ingest endpoint; it is the project's domain name for capture).
- `POST /oracle/rank`: declare `responses={501: ...}`, mark it `deprecated=True`, and drop its fake 200.

**Rationale**: No custom `openapi()` override. The document stays a pure function of the route declarations.

## R5. Business-error shape and codes (FR-008a)

**Decision**: New module `jobforce/routers/errors.py` containing:
- `ErrorCode(StrEnum)`: the single catalog (see [contracts/error-codes.md](contracts/error-codes.md)). Each member maps to its HTTP status.
- `ApiError(Exception)` carrying `code` and `detail`, and `api_error_handler` registered in `create_app()`. The handler returns `JSONResponse(status, {"detail": detail, "code": code})`.
- `BusinessError(BaseModel)`: `detail: str`, `code: ErrorCode`. It appears in the spec with the code list as an `enum`, which satisfies "listed once".
- `error_responses(*codes) -> dict[int, dict]`: groups codes by status and emits `{"model": BusinessError, "description": "<codes>: <meaning>"}`. For a 422 it emits `anyOf [BusinessError, HTTPValidationError]`, because supplying a custom 422 stops FastAPI from adding its default one.

Every `raise HTTPException(...)` in `routers/` becomes `raise ApiError(ErrorCode.X, "<same detail text>")`, and the `INVALID_TRANSITION` `JSONResponse` becomes the same.

**Rationale**: One catalog drives both runtime bodies and documentation, so they can't diverge. Keeping the `detail` text byte-identical means the existing contract tests stay green (FR-014). Specific codes (`JOB_NOT_FOUND` rather than a generic `NOT_FOUND`) let skills branch without parsing text.

**Alternatives considered**:
- *Subclass `HTTPException` with `detail=dict`*: changes `detail` from a string to an object, which breaks consumers.
- *A generic `NOT_FOUND` for every 404*: less useful, since the endpoint already implies the resource in most cases but not all (`/resume/{id}/export` can be resume-missing or base-missing).

## R6. Resume `structured_data` typed but permissive (FR-011a)

**Decision**: Define Pydantic models `ResumeStructuredData`, `PersonalInfo`, `WorkHistoryItem`, `EducationItem`, `ProjectItem`, `CertificationItem` (new module `jobforce/routers/resume_schema.py`). Every field is optional and each uses `model_config = ConfigDict(extra="allow")`. Fields use `SkipValidation[ResumeStructuredData]` on `ResumeOut`, `TailorRequest` and the `PUT /resume/base` body, so the schema is emitted as a named component but no input or output is validated against it.

**Verification required during implementation** (test-first):
- A resume with extra keys, missing keys and wrong-typed values (e.g., `skills` as an object) round-trips through `PUT /resume/base` → `GET /resume/base` unchanged, with status 200.
- No `PydanticSerializationUnexpectedValue` warnings on that path (pytest `-W error::UserWarning` on that test).

**Fallback** if `SkipValidation` emits serializer warnings: keep the runtime type `dict[str, Any]` and add `WithJsonSchema({"$ref": "#/components/schemas/ResumeStructuredData"})`, then register the component through `app.openapi_schema` post-processing in one small function. Record the choice in the plan's Complexity Tracking if this fallback is used.

**Alternatives considered**: Strict validation (rejected in clarification Q3); `Any` (rejected in Q3).

## R7. Enum-like string fields

**Decision**: Document allowed values without adding runtime validation: `Annotated[str, WithJsonSchema({"type": "string", "enum": [...]})]` for `PipelineStatus`, `RoleType`, `FitConfidence` and `QuestionCategory`. Source the value lists from existing backend constants (e.g., the states in `services/scout.py::_VALID_TRANSITIONS`) so they can't drift.

**Rationale**: The generated TS types become literal unions, which the frontend already relies on, and nothing that's accepted today gets rejected (FR-014). Without this, generated types would widen to `string` and the frontend would have to hand-narrow them, recreating parallel types (SC-007).

## R8. Frontend type generation (FR-016–FR-018)

**Decision**:
- Add `openapi-typescript@^7.13.0` as a frontend devDependency.
- Add `npm run gen:api`, which runs `openapi-typescript ../backend/openapi.yaml -o src/lib/api-schema.d.ts`. The output is checked in and excluded from ESLint.
- Add `npm run check:api`, a small `scripts/check-api-types.mjs` that runs the programmatic `openapiTS()` + `astToString()` and diffs the result against the file. It exits 1 with `run: cd frontend && npm run gen:api`.
- Add `npm run typecheck`, which runs `tsc --noEmit`.
- `src/lib/types.ts` becomes re-exports and aliases (`export type JobListing = Schemas["JobListingOut"]`) and keeps only frontend-only types. Every one of the 18 importing files keeps its import path unchanged.
- Root `make check` frontend step becomes `npm run check:api && npm run typecheck && npm run lint && npm test`. Root `make openapi` runs backend `make openapi` and then frontend `npm run gen:api`.

**Rationale**: `openapi-typescript` is zero-runtime (types only), supports 3.1, and its output is deterministic (no timestamp). Using re-exports keeps the frontend change mechanical.

**Expected friction**: generated shapes are more honest than the hand-written ones. For example `personal_info` becomes optional, and `ResumeStructuredData` gains `coursework` and `patents`. Expect a handful of `?.` and null-guard fixes in forge components. These are real latent bugs, fixed in this feature.

**Alternatives considered**:
- `openapi-typescript-codegen` / `orval`: generate clients too, which is out of scope (clarification Q1).
- A Jest test for drift: works, but a plain script gives a clearer failure message and is faster.

## R9. Documentation pointers (FR-015)

**Decision**: Add a short "API contract" subsection to `CLAUDE.md` naming `backend/openapi.yaml`, `make openapi`, and `frontend/src/lib/api-schema.d.ts`. Keep the existing "Notable API Endpoints" table, because CLAUDE.md is loaded into every session and skills depend on it, but add a line saying the spec is authoritative. Also update `DEVELOPMENT.md` and fix CLAUDE.md's claim that `npm run lint` includes a TS check.
