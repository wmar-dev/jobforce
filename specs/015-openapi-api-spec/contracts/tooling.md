# Contract: Generation and Check Commands

## Backend

| Command | Behavior | Exit |
| --- | --- | --- |
| `cd backend && make openapi` | Runs `python -m jobforce.cli.export_openapi`, which writes `backend/openapi.yaml` | 0 |
| `python -m jobforce.cli.export_openapi --check` | Compares the generated document to the file without writing | 0 if identical; 1 with `openapi.yaml is out of date — run: cd backend && make openapi` |
| `make check` (backend) | Now also runs `tests/contract/test_openapi_drift.py` and `test_openapi_completeness.py` | non-zero on drift or an incomplete endpoint |

`export_openapi` requires no `config.yaml`, no database and no network. Its output is byte-identical across runs and machines: YAML, insertion order, `\n` line endings, trailing newline, and no `servers` key.

## Frontend

| Command | Behavior | Exit |
| --- | --- | --- |
| `npm run gen:api` | Runs `openapi-typescript ../backend/openapi.yaml -o src/lib/api-schema.d.ts` | 0 |
| `npm run check:api` | Runs `node scripts/check-api-types.mjs`, which regenerates in memory and compares | 0 if identical; 1 with `api-schema.d.ts is out of date — run: cd frontend && npm run gen:api` |
| `npm run typecheck` | Runs `tsc --noEmit` | non-zero on type errors |

## Root

| Command | Behavior |
| --- | --- |
| `make openapi` | Runs backend `make openapi`, then frontend `npm run gen:api` |
| `make check` | Frontend step becomes `npm run check:api && npm run typecheck && npm run lint && npm test` |

## Completeness rules enforced by `test_openapi_completeness.py`

For every operation in `openapi.yaml`:

1. `summary` is non-empty and at most 80 characters.
2. `description` is non-empty.
3. `tags` has exactly one entry, and that tag has a description in the top-level `tags` list.
4. At least one 2xx response. Each 2xx except 204 has an `application/json` schema that is not `{}`. A 204 has no content. *Exception:* a `deprecated` operation that only ever returns an error (`POST /oracle/rank`, 501).
5. Every `parameters[*]` entry has a non-empty `description`.
6. Every response with status ≥ 400 other than 422 references `BusinessError`. A 422 response, where present, is either `HTTPValidationError` alone or `anyOf[BusinessError, HTTPValidationError]`, with no sibling `$ref`. *Exception:* `POST /ingest` 409 returns the existing listing (`IngestResponse`), not an error body.

Document-wide:

7. `components.schemas.BusinessError.properties.code.enum` equals the `ErrorCode` members exactly.
8. `components.schemas.ResumeStructuredData` exists and has the 9 known top-level properties, none of them required.
9. `info.title == "Jobforce API"`, and `info.version` matches `pyproject.toml` `[project].version`.
