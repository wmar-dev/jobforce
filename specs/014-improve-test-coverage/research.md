# Phase 0 Research: Improve Test Coverage for Jobs Router and Coach Service

## Decision 1: The measured coverage gap is mostly a tooling bug, not a testing gap

**Decision**: Before writing new tests, fix `[tool.coverage.run]` in `backend/pyproject.toml` by adding
`concurrency = ["greenlet", "thread"]`.

**Rationale**: `coverage.py` 7.16 (used via `pytest-cov`) traces execution with `sys.monitoring` on Python
3.12 by default. SQLAlchemy's async engine bridges the sync-style `aiosqlite` driver into async code using
the `greenlet` library's stack-switching, and the default tracer does not follow execution across a greenlet
switch unless `concurrency` explicitly lists `"greenlet"`. In practice this meant any line inside an `async`
service function that runs *after* an `await session.commit()` / `await session.refresh()` / `await
session.get()` call was liable to be silently under-counted as "missing" even when a passing test already
executed it.

This was verified empirically, with no test changes:

| Module | Coverage before config fix | Coverage after config fix (same tests) |
|---|---|---|
| `jobforce/routers/jobs.py` | 62% | 92% |
| `jobforce/services/coach.py` | 48% | 76% |

**Alternatives considered**:
- *Write tests to directly re-exercise the lines already covered but misreported* — rejected: wasteful, and
  leaves the same measurement bug in place for the next feature that touches an async service.
- *Switch the test database driver away from a greenlet-bridged async driver* — rejected: unrelated to the
  actual goal and a much larger, riskier change than a one-line coverage config fix.
- *Ignore the tooling issue and just chase the reported percentage* — rejected: produces redundant tests and
  a permanently misleading coverage signal for future features.

**Consequence for scope**: the real remaining gap after the config fix is much smaller than the original 62%/48%
suggested. The tasks phase should apply the config fix first, re-run coverage to confirm the new baseline, and
then write only the tests needed to close the genuinely uncovered branches identified below.

## Decision 2: Where new tests belong

**Decision**: Close the remaining `routers/jobs.py` gaps by extending the existing contract-test file
(`backend/tests/contract/test_jobs.py`), using the repo's established pattern (`test_client` fixture +
`_ingest` helper + direct `GET`/`PATCH`/`DELETE` calls). Close the remaining `services/coach.py` gaps mostly
the same way, extending `backend/tests/contract/test_coach.py` — **except** for the "stored summary present"
and "stored summary present but malformed" branches in `get_session_summary_data`, which need a new direct
service-level test file, `backend/tests/services/test_coach.py`, following the existing
`tests/services/test_oracle.py` pattern (call the service function directly against a seeded `db_session`).

**Rationale**: Nothing in the current application ever writes `InterviewSession.overall_summary` — it is a
column that exists for a future feature but is always `NULL` today (confirmed: `grep -rn overall_summary
jobforce/` only finds the column definition and the one read site). There is therefore no API path to set it,
so the only way to exercise "a summary was stored" and "a malformed summary was stored" is to seed the column
directly via `db_session`, which is a service-level concern, not a contract-level one.

**Alternatives considered**:
- *Add a new endpoint or debug hook to set `overall_summary` for testability* — rejected: this spec is
  test-only and must not add API surface (see spec.md Assumptions).
- *Skip those two branches* — rejected: they're explicit acceptance scenarios in User Story 5 / FR-013 and
  a real (if currently dormant) fallback behavior worth locking down.

## Decision 3: No new contracts, data model, or API surface

**Decision**: Skip generating a `contracts/` directory or new entity definitions for this feature.

**Rationale**: The feature adds zero new endpoints, request/response fields, or database columns — it adds
test coverage for behavior that already exists and is already documented (CLAUDE.md's "Notable API
Endpoints" table, `backend/jobforce/db/models.py`). Generating placeholder contract files for endpoints that
aren't changing would just duplicate existing documentation.

**Alternatives considered**: Writing out full OpenAPI-style contract files for the six job endpoints and four
coach functions under test — rejected as unnecessary duplication of `backend/jobforce/routers/*.py` and
CLAUDE.md, which already serve as the source of truth for these contracts.
