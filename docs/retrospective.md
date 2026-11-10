# Jobforce Retrospective

## What Worked Well

- [ ] List things that went smoothly in this sprint or feature
- [ ] Tools and processes that reduced friction
- [ ] Patterns that should be repeated

## What to Improve

- [ ] List things that caused delays or rework
- [ ] Processes that need adjustment
- [ ] Technical debt created and why

## Recurring Failure Patterns

- [ ] Test failures that surfaced the same root cause multiple times
- [ ] Integration issues that were predictable in hindsight
- [ ] Gaps between spec and implementation that required rework

## Action Items

| Item | Owner | Priority | Status |
|------|-------|----------|--------|
| (add rows) | | | |

---

## 015 — OpenAPI specification (2026-11-09)

### What worked well

- Generating the spec from FastAPI's own route declarations plus a pytest drift test meant no new gate wiring: `make check` caught a stale `openapi.yaml` on the first route edit.
- One `ErrorCode` catalog that drives both runtime bodies and the docs kept them in sync by construction. Keeping `detail` text byte-identical meant no existing contract test needed editing.
- The generated frontend types found real defects right away: the Oracle page rendered `fit_rationale`, which the list endpoint never returns, and an unused `useProfile` hook called a non-existent `/api/profile`.

### What to improve

- Research R6's primary approach (`SkipValidation[Model]`) failed as the risk table predicted: Pydantic serializer warnings on non-conforming resumes. The fallback (runtime `Any` plus `allOf: [$ref]` plus one `app.openapi` wrapper) works. A bare `$ref` in `WithJsonSchema` crashes Pydantic because it tries to resolve it locally.
- FastAPI merges a `responses[...]["model"]` into custom `content` as a sibling `$ref`. For 422 (anyOf business|validation) the model must be omitted. Completeness rule 6 now asserts this.
- FastAPI drops `WithJsonSchema` enums on query parameters. The status/role_type filters list their allowed values in the description instead.
- `openapi-typescript@7.13.0` declares `peer typescript@^5` while the frontend is on TS 6. Resolved with an npm `overrides` entry (no `--legacy-peer-deps`); generated output is unaffected. Revisit when openapi-typescript ships a TS 6 peer range.

### Action items

| Item | Owner | Priority | Status |
| --- | --- | --- | --- |
| Decide whether `GET /jobs` list items should include `fit_rationale` (Oracle page rationale, removed as dead UI) | Warren | Medium | Open |
| Drop the `openapi-typescript` TypeScript override once a TS 6-compatible release exists (`/housekeeping`) | Warren | Low | Open |
| Consider generating a typed fetch client to replace `frontend/src/lib/api.ts` wrappers (out of scope for 015) | Warren | Low | Open |
