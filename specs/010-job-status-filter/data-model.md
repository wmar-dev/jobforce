# Data Model: Job Status Filtering & Triage

## Changed Entity: JobListing

### Status field

The `status` column on `job_listings` is extended with two new values:

| Value | Meaning | Terminal? |
|---|---|---|
| `saved` | Crawled, not yet triaged | No |
| `archived` | Dismissed / low relevance | No (restorable) |
| `shortlisted` | Intent to apply | No (can advance or revert) |
| `applied` | Application submitted | No |
| `interviewing` | In interview process | No |
| `offer` | Offer received | Yes |
| `rejected` | Rejected | Yes |
| `withdrawn` | Withdrawn by user | Yes |

### Updated `_VALID_STATUSES` (backend)

```python
_VALID_STATUSES = "('saved','applied','interviewing','offer','rejected','withdrawn','archived','shortlisted')"
```

### Updated `_VALID_TRANSITIONS` (backend)

```python
_VALID_TRANSITIONS = {
    "saved":        ["applied", "rejected", "withdrawn", "archived", "shortlisted"],
    "archived":     ["saved"],
    "shortlisted":  ["applied", "rejected", "withdrawn", "archived", "saved"],
    "applied":      ["interviewing", "rejected", "withdrawn"],
    "interviewing": ["offer", "rejected", "withdrawn"],
    "offer":        [],
    "rejected":     [],
    "withdrawn":    [],
}
```

### Updated `PipelineStatus` (frontend)

```typescript
export type PipelineStatus =
  | "saved"
  | "applied"
  | "interviewing"
  | "offer"
  | "rejected"
  | "withdrawn"
  | "archived"
  | "shortlisted";
```

---

## Default Query Behaviour Change

`GET /api/jobs` with no `status` filter currently returns all statuses. After this feature:

- Default behaviour excludes `archived` — the query adds `WHERE status != 'archived'` when no status filter is provided.
- Passing `status=archived` explicitly shows only archived jobs.
- Passing `status=all` (frontend "All" tab) will need to either send no status param (and accept default exclusion) OR the frontend "All" tab should be renamed/split — see contracts.

---

## New Endpoint: Bulk Archive

```
POST /api/jobs/bulk-archive
```

No request body required. Internally:
- Selects all `job_listings` WHERE `status = 'saved'` AND `fit_score IS NOT NULL` AND `fit_score < 0.50`
- Updates each to `status = 'archived'`
- Creates a `status_transitions` row for each (from_status=`saved`, to_status=`archived`)
- Returns: `{ "archived_count": N }`

Note: `fit_score` is stored as a float 0.0–1.0 internally; the user-facing threshold of 50 corresponds to `fit_score < 0.50`.

---

## Migration: `010_add_triage_statuses.sql`

SQLite does not support modifying CHECK constraints in place. The migration recreates the `job_listings` table with the updated constraint.

```sql
-- 010_add_triage_statuses.sql
PRAGMA foreign_keys = OFF;

BEGIN TRANSACTION;

CREATE TABLE job_listings_new (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    title       TEXT    NOT NULL,
    location    TEXT,
    role_type   TEXT,
    description TEXT,
    source_url  TEXT    NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'saved'
                CHECK(status IN ('saved','applied','interviewing','offer','rejected','withdrawn','archived','shortlisted')),
    fit_score   REAL,
    fit_scored  INTEGER NOT NULL DEFAULT 0,
    fit_confidence TEXT,
    fit_rationale  TEXT,
    crawled_at  TEXT,
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

INSERT INTO job_listings_new SELECT
    id, company_id, title, location, role_type, description, source_url,
    status, fit_score, fit_scored, fit_confidence, fit_rationale,
    crawled_at, created_at, updated_at
FROM job_listings;

DROP TABLE job_listings;
ALTER TABLE job_listings_new RENAME TO job_listings;

CREATE INDEX idx_job_listings_company ON job_listings(company_id);
CREATE INDEX idx_job_listings_status  ON job_listings(status);

COMMIT;

PRAGMA foreign_keys = ON;
```

---

## StatusTransition (unchanged)

No schema changes needed. Every archive/shortlist/restore action records a row in `status_transitions` via the existing `transition_status()` service function.
