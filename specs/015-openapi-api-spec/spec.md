# Feature Specification: OpenAPI Specification for the Jobforce API

**Feature Branch**: `015-openapi-api-spec`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "Add openapi specification for api"

## Clarifications

### Session 2026-11-09

- Q: Should the specification drive generated code for consumers? → A: Yes. Generate frontend TypeScript types from the specification; the frontend's hand-written types use or re-export them; the quality gate fails if the generated types are out of date. A generated fetch client and types for the extension stay out of scope.
- Q: How should the inconsistent error responses be handled? → A: Document one shared business-error shape `{detail: string, code?: string}` and add a stable machine-readable `code` to every business-rule error. Existing `detail` text and status codes stay the same (business-rule 422s stay 422).
- Q: How should the resume's `structured_data` be described? → A: Describe the full known shape (personal_info, summary, skills, work_history, education, projects, certifications, coursework, patents, and their nested fields) so generated types use it. The server stays permissive: extra keys allowed, all keys optional, no new rejections.

## User Scenarios & Testing *(mandatory)*

The Jobforce API has three kinds of consumers: the web dashboard, the Chrome extension, and the Claude Code skills (Oracle, Forge, Scout, Coach) that read and write through it. Today the API's contract is only discoverable by running the server and visiting its live docs page, or by reading the endpoint table in the project's guidance file and the route code. Some endpoints don't declare what they return, and error responses (such as the invalid status transition error) aren't documented. This feature makes the API contract a first-class, version-controlled artifact that is complete, accurate, and kept in sync with the running API.

### User Story 1 - Checked-in, always-current API contract (Priority: P1)

As the developer (or a Claude Code skill working in the repo), I can open a single API specification file in the repository and see every endpoint, its inputs, and its outputs, without starting the server. If someone changes an endpoint and forgets to update the file, the project's quality gate fails.

**Why this priority**: A contract that drifts from reality is worse than none. A checked-in file that is verified on every quality-gate run is the foundation the other stories build on, and on its own it already lets skills and reviewers read the contract offline and see API changes in diffs.

**Independent Test**: Run the regeneration command and confirm the file appears in the repository. Change an endpoint's response shape without regenerating, run the quality gate, and confirm it fails with a message naming the out-of-date file and the command that fixes it.

**Acceptance Scenarios**:

1. **Given** a fresh checkout, **When** the developer opens the API specification file, **Then** it lists every endpoint the running API serves, with matching paths, methods, parameters, request bodies, and response shapes.
2. **Given** an endpoint has been added, removed, or changed and the specification file has not been regenerated, **When** the developer runs the project quality gate, **Then** the gate fails and tells them which command regenerates the file.
3. **Given** the specification file is up to date, **When** the developer runs the quality gate, **Then** the specification check passes and adds no noticeable time to the run.
4. **Given** the developer runs the regeneration command twice with no API changes, **When** they compare the results, **Then** the file is byte-for-byte identical, so diffs show only real contract changes.

---

### User Story 2 - Complete, self-explanatory documentation for every endpoint (Priority: P2)

As a consumer of the API (a skill author, the frontend, or the extension), each endpoint in the specification tells me what it does, what it returns on success, and what errors it can return and why, so I don't need to read route code to call it correctly.

**Why this priority**: The value of the contract depends on its content. Several endpoints currently return untyped payloads, and documented business rules (e.g., status changes only through the dedicated status endpoint; bulk-archive option rules) live only in prose elsewhere. Without this story, the file from Story 1 is accurate but thin.

**Independent Test**: Review the generated specification and confirm every endpoint has a summary, a description, a typed success response, and documented error responses; an automated check enforces this so new endpoints can't omit them.

**Acceptance Scenarios**:

1. **Given** any endpoint in the specification, **When** a consumer reads it, **Then** it has a one-line summary, a description of its behavior, and a declared response shape for every success status it can return (including "no content" responses).
2. **Given** an endpoint can reject a request for a business reason (e.g., an invalid pipeline status transition, mutually exclusive bulk-archive options, merging a company into itself, a missing HTML snapshot for reparse), **When** a consumer reads it, **Then** the specification lists that error status, the shared business-error shape, and the specific error code(s) it can return.
3. **Given** the endpoints, **When** a consumer browses the specification, **Then** endpoints are grouped by domain (jobs, companies, resume/forge, oracle, coach, ingest, dashboard) with a short description of each group.
4. **Given** a developer adds a new endpoint without a summary or typed response, **When** they run the quality gate, **Then** the gate fails and identifies the incomplete endpoint.
5. **Given** endpoints with non-obvious query parameters (e.g., exact-match source URL lookup, company substring filter, bulk-archive modes), **When** a consumer reads them, **Then** each parameter has a description of its effect and constraints.

---

### User Story 3 - The specification is the single source for consumers (Priority: P3)

As a skill author or someone working in the repo, the project guidance and developer docs point me to the specification as the authoritative API reference, rather than duplicating endpoint details by hand in several places. As the frontend developer, the dashboard's API data types are generated from the specification, so a backend change that breaks the frontend shows up as a compile error instead of a runtime bug.

**Why this priority**: Reduces duplicated, drifting documentation, but delivers value only once Stories 1–2 make the specification trustworthy.

**Independent Test**: Read the project guidance and developer docs and confirm they reference the specification file's location and regeneration command. Change a response field in the backend, regenerate, and confirm the frontend type check fails where the field is used.

**Acceptance Scenarios**:

1. **Given** the project guidance file, **When** a reader looks for API details, **Then** it names the specification file's location and how to regenerate it.
2. **Given** the endpoint behaviors currently described only in prose (status-change rules, bulk-archive modes, merge, reparse, source-URL lookup), **When** the feature is complete, **Then** those behaviors are captured in the specification itself.
3. **Given** a backend change renames or retypes a response field the frontend uses, **When** the developer regenerates the specification and the frontend types, **Then** the frontend fails to compile at every place that uses the old field, before anything runs.
4. **Given** the frontend's API data types, **When** a developer looks for where an API shape is defined, **Then** it comes from the generated types, not from a hand-written copy.

---

### Edge Cases

- **Endpoints with no response body** (delete, delete note): documented as "no content" success responses, not omitted.
- **Validation errors on any input**: the generic input-validation error shape is documented once and referenced, not repeated per endpoint.
- **Same status, two shapes**: a 422 can be either an input-validation error (list-shaped `detail`) or a business-rule error (string `detail` + `code`). The specification documents both for endpoints that can return either, and consumers tell them apart by the presence of `code`.
- **Resume structured data**: described with its full known shape, but every key is optional and extra keys are allowed. A resume with extra or missing keys is accepted exactly as today, and generated frontend types mark those keys optional.
- **Endpoints intentionally excluded from the public contract** (e.g., internal or health endpoints, if any): explicitly marked or excluded so the completeness check doesn't flag them.
- **Environment-dependent values** (server address, version string): must not make the regenerated file differ between machines or runs.
- **Regeneration must not need a database, configuration file, or network access**, so it works in a fresh checkout and in CI.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain a single version-controlled API specification file in the OpenAPI format describing every endpoint the API serves.
- **FR-002**: The specification file MUST be generated from the API's own definitions, not maintained by hand, so it can't diverge from the implementation.
- **FR-003**: The project MUST provide one command that regenerates the specification file.
- **FR-004**: Regeneration MUST be deterministic: repeated runs with no API change produce identical output on any machine.
- **FR-005**: Regeneration MUST work without a running server, database, configuration files, or network access.
- **FR-006**: The project quality gate MUST fail when the checked-in specification differs from what the current API definitions would generate, and the failure message MUST name the regeneration command.
- **FR-007**: Every endpoint in the specification MUST have a summary, a description, and a declared response shape for each success status it returns.
- **FR-008**: Every endpoint that can return a business-rule error (not-found, invalid transition, conflicting options, etc.) MUST document that status, the shared business-error shape, and the error code(s) it can return.
- **FR-008a**: Every business-rule error MUST return the shared business-error shape: a human-readable `detail` string plus a stable, machine-readable `code` (e.g., `NOT_FOUND`, `INVALID_TRANSITION`, `SELF_MERGE`, `CONFLICTING_OPTIONS`, `MISSING_REQUIRED_OPTION`, `NO_SNAPSHOT`). The set of codes MUST be listed once in the specification. Input-validation errors keep their existing list-shaped `detail` and are documented as a separate shape.
- **FR-009**: Every query and path parameter MUST have a description; parameters with constraints (allowed values, mutual exclusivity, "requires X") MUST state them.
- **FR-010**: Endpoints MUST be grouped by domain, and each group MUST have a short description.
- **FR-011**: The quality gate MUST fail if any endpoint lacks a summary or a declared success response shape (FR-007), so new endpoints can't silently go undocumented.
- **FR-011a**: The resume's structured data MUST be described as a named shared data shape with its known top-level keys (personal_info, summary, skills, work_history, education, projects, certifications, coursework, patents) and their nested fields (e.g., work_history entries: company, title, start_date, end_date, location, bullets). All keys MUST be optional, and extra keys MUST be allowed; the server MUST NOT reject any resume payload it accepts today.
- **FR-012**: The specification MUST carry the API's title and a version identifier.
- **FR-013**: The live interactive docs page the API already serves MUST continue to work and MUST reflect the same content as the checked-in file.
- **FR-014**: Apart from adding `code` to business-rule error bodies (FR-008a), this feature MUST NOT change any endpoint's runtime behavior: paths, methods, status codes, success response bodies, and existing error `detail` text stay the same, and existing tests continue to pass.
- **FR-015**: The project guidance file and developer docs MUST reference the specification file's location and regeneration command.
- **FR-016**: The frontend's API data types MUST be generated from the checked-in specification by a single command, and that command MUST be deterministic.
- **FR-017**: The frontend's existing type module MUST use or re-export the generated types for every API request/response shape it covers, so frontend code keeps its current imports and no API shape is hand-maintained in parallel. Frontend-only types (UI state, display helpers) may stay hand-written.
- **FR-018**: The quality gate MUST fail when the generated frontend types differ from what the current specification would produce, and when frontend code doesn't compile against them.

### Key Entities

- **API Specification Document**: The single checked-in description of the API contract. Contains the API title and version, domain groups, every endpoint, and shared data shapes. Generated, never hand-edited.
- **Endpoint Entry**: One path and method in the document, with summary, description, domain group, parameters, request body shape, success responses, and error responses.
- **Shared Data Shape**: A reusable description of a request or response body (e.g., job listing, company, resume, resume structured data, status transition, prep session, business-error body) that endpoint entries reference instead of repeating.
- **Error Response**: A documented failure outcome. There are two shapes: the business-error shape (`detail` string + `code` from a fixed, documented list) and the input-validation shape (list of field errors).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of endpoints served by the API appear in the checked-in specification, and the specification describes no endpoint the API doesn't serve.
- **SC-002**: 100% of endpoints have a summary, a description, and a declared success response shape (today 4 of 29 routes declare no response shape and none have summaries).
- **SC-003**: Every known business-rule error (invalid status transition, conflicting bulk-archive options, self-merge, missing reparse snapshot, not-found cases) is documented on the endpoints that return it, and 100% of them return a `code` (today only 1 of ~30 does).
- **SC-004**: An API change that isn't reflected in the specification is caught by the quality gate in 100% of cases, before commit.
- **SC-005**: A skill author can find how to call any endpoint, including its error cases, from the specification alone, without reading route code.
- **SC-006**: Regenerating the specification and the frontend types takes under 10 seconds and needs no setup beyond installing project dependencies.
- **SC-007**: 100% of the API request/response shapes the frontend uses come from generated types; 0 remain hand-maintained in parallel.

## Assumptions

- **Single consumer group, no external publishing**: Jobforce is a personal, local-only tool. The specification is for the developer, the frontend, the extension, and Claude Code skills; it is not published to an external portal, and no authentication scheme needs to be documented (the API has none).
- **Generated, not design-first**: The API already exists, so the specification is derived from the implementation and enriched there, rather than authored first and used to generate server code.
- **Generated frontend types, not a generated client**: Frontend data types are generated from the specification (FR-016–FR-018). Generating a typed fetch client to replace the frontend's hand-written fetch wrappers, and generating types for the Chrome extension, are out of scope and left as follow-ups.
- **Format and location**: The document uses the OpenAPI version the API's framework emits natively, is stored in a human-readable, diff-friendly format, and lives alongside the backend.
- **The quality gate is the enforcement point**: The drift and completeness checks run as part of the existing `make check` flow, not as a separate step developers must remember.
- **Response contents stay the same**: Where an endpoint today returns an untyped payload, declaring its shape documents existing behavior; it doesn't redesign the payload.
