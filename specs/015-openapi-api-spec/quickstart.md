# Quickstart: Validating the OpenAPI Specification Feature

Run these from the repo root after implementation. Each block maps to a user story or requirement.

## 1. Generate and inspect (US1, FR-001–FR-005)

```bash
mv config.yaml /tmp/cfg.bak            # prove no config is needed
make openapi                           # writes backend/openapi.yaml + frontend/src/lib/api-schema.d.ts
mv /tmp/cfg.bak config.yaml
git status --short backend/openapi.yaml frontend/src/lib/api-schema.d.ts   # no diff if already current
make openapi && git diff --exit-code   # determinism: second run is byte-identical
grep -c "operationId:" backend/openapi.yaml   # expect 29
```

## 2. Drift is caught (US1, FR-006, SC-004)

```bash
# Add a throwaway field to a response model, e.g. JobListingOut.foo: str = "x"
cd backend && make check     # FAILS: "openapi.yaml is out of date — run: cd backend && make openapi"
make openapi && make check   # backend passes
cd .. && make check          # FAILS at check:api: "api-schema.d.ts is out of date — run: cd frontend && npm run gen:api"
git checkout -- backend/ frontend/   # revert the experiment
```

## 3. Completeness is enforced (US2, FR-007–FR-011)

```bash
# Add a new route with no summary and no response_model
cd backend && uv run pytest tests/contract/test_openapi_completeness.py -x
# FAILS naming "GET /api/<route>: missing summary"
```

## 4. Business error codes at runtime (FR-008a, SC-003)

```bash
make dev   # in another terminal
curl -s -X PATCH localhost:8000/api/jobs/999999/status -H 'content-type: application/json' \
  -d '{"status":"applied"}' | jq      # {"detail":"Job listing not found","code":"JOB_NOT_FOUND"}
curl -s -X POST "localhost:8000/api/jobs/bulk-archive?all_active=true" | jq
                                      # {"detail":"all_active/saved_only requires company_id","code":"MISSING_COMPANY_ID"}
curl -s -X PATCH localhost:8000/api/jobs/abc | jq   # validation error: list-shaped detail, no "code"
grep -rn "HTTPException(" backend/jobforce/routers/   # expect: no results
```

## 5. Resume stays permissive (FR-011a)

```bash
cd backend && uv run pytest tests/contract/test_forge.py -k permissive -xvs
# Round-trips a resume with extra keys, missing keys, and skills-as-object, unchanged, with no warnings
```

## 6. Frontend compiles against generated types (US3, FR-016–FR-018, SC-007)

```bash
cd frontend && npm run check:api && npm run typecheck && npm run lint && npm test
grep -n "^export interface" src/lib/types.ts   # only frontend-only types remain
```

## 7. Live docs still work (FR-013)

Open <http://localhost:8000/docs>. The endpoints are grouped by the 7 tags, each with a description. `POST /oracle/rank` is shown as deprecated. Error responses list their codes.

## 8. Full gate

```bash
make check
grep -r "import anthropic" backend/   # still zero results
```
