# Research: Job Status Filtering & Triage

## Decision 1: Status extension approach

**Decision**: Extend `_VALID_STATUSES` string and `_VALID_TRANSITIONS` dict in `backend/jobforce/services/scout.py` and `backend/jobforce/db/models.py`; add a SQLite migration for the constraint change.

**Rationale**: The existing pattern uses a plain `CheckConstraint` string and a dict-based transition graph. Adding new statuses requires updating both constants and the SQLite check constraint via a migration — SQLite doesn't support `ALTER TABLE ... DROP CONSTRAINT`, so the migration must recreate the table or use a workaround (PRAGMA defer_foreign_keys + recreate). Simplest approach for SQLite: add new statuses to the constraint string and run `CREATE TABLE ... RENAME` migration pattern.

**Alternatives considered**: Enum type — not supported in SQLite without workarounds; not worth the complexity. Separate triage_status column — adds redundancy; single status column is cleaner.

---

## Decision 2: SQLite migration strategy for CHECK constraint change

**Decision**: Use the standard SQLite migration pattern: create new table with updated constraint, copy data, drop old table, rename. Encapsulate in `010_add_triage_statuses.sql`.

**Rationale**: SQLite does not support `ALTER TABLE DROP CONSTRAINT` or `ALTER TABLE MODIFY COLUMN`. The safe pattern is: (1) create new table with updated schema, (2) `INSERT INTO new SELECT * FROM old`, (3) `DROP TABLE old`, (4) `ALTER TABLE new RENAME TO old`. This is the only reliable approach for SQLite constraint changes.

**Alternatives considered**: Ignore constraint and let app-layer enforce — risky, leaves DB in inconsistent state if constraint matters for data integrity. PRAGMA disable check constraints — not reliable across all SQLite versions.

---

## Decision 3: Default view filtering (exclude archived)

**Decision**: Change the backend `GET /api/jobs` default query to exclude `archived` status unless explicitly requested. Add `include_archived: bool = False` query param, OR simply allow the existing `status` filter to handle it — if no status is passed, exclude archived by default.

**Rationale**: The jobs page currently defaults to `status=all` (no filter), which returns everything. The spec requires archived jobs to be hidden by default. The cleanest approach is to add a backend-level default exclusion: when no status filter is passed, add `WHERE status != 'archived'`. When `status=archived` is explicitly passed, show only archived. This requires no new query param and is consistent with existing filter behavior.

**Alternatives considered**: Frontend-only filter — fragile; archived jobs still returned in pagination counts, total, etc. New `include_archived` boolean param — adds complexity; existing `status` filter already handles inclusion/exclusion cleanly.

---

## Decision 4: Bulk archive endpoint

**Decision**: New endpoint `POST /api/jobs/bulk-archive` that archives all `saved` jobs with `fit_score < 50`, skipping `shortlisted` jobs. Returns count of archived jobs.

**Rationale**: Bulk operations belong on the backend (single DB transaction, atomic). A dedicated endpoint is cleaner than a PATCH-many pattern. Only `saved` jobs are candidates — `shortlisted` jobs are explicitly excluded, and pipeline-stage jobs (`applied`, etc.) should not be touched.

**Alternatives considered**: Frontend loop over individual PATCH calls — not atomic, slow for many jobs. Generic bulk PATCH endpoint — over-engineered for one use case.

---

## Decision 5: Inline action UX pattern

**Decision**: Add a small action menu (or two icon buttons) on each job row in `JobTable.tsx` — an archive button (🗂 or X) and a shortlist button (⭐ or bookmark). Actions call `PATCH /api/jobs/{id}/status`.

**Rationale**: The spec requires one-action archive/shortlist from the list view (SC-002, SC-003, FR-011). The existing `JobTable` row already has title, company, status badge, fit score. Adding two small icon buttons in a new "Actions" column is the minimal change. Uses the existing `patchJobStatus` API function.

**Alternatives considered**: Dropdown context menu — extra click, not "one action". Swipe gesture — not applicable on desktop dashboard.

---

## Decision 6: Transition graph update

**Decision**: Extend `_VALID_TRANSITIONS` as follows:
- `saved` → add `archived`, `shortlisted`
- `archived` → add `saved` (restore)
- `shortlisted` → add `applied`, `archived`, `saved` (full flexibility)

**Rationale**: The spec requires: archive from saved/shortlisted (FR-004), restore from archived (FR-005), shortlist from saved/archived (FR-003). The transition graph must encode all these paths. Shortlisted behaves like an "active" pre-application state so it should allow forward to `applied` and backward to `saved`/`archived`.

**Alternatives considered**: Allow any-to-any transitions for triage statuses — too permissive; current graph guards pipeline integrity.

---

## Decision 7: Coach page filter expansion

**Decision**: In `frontend/src/app/coach/page.tsx`, add a third `getJobs({ status: "shortlisted", limit: 50 })` fetch alongside the existing `applied` and `interviewing` fetches.

**Rationale**: Spec FR-012 requires shortlisted jobs on Coach. The page currently `Promise.all`s two fetches; adding a third is the minimal change. Shortlisted jobs are pre-application intent, so prep material is valuable at that stage.

**Alternatives considered**: Fetch all statuses and filter client-side — wasteful; existing pattern of separate fetches per status is cleaner.
