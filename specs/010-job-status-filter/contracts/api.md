# API Contracts: Job Status Filtering & Triage

## Changed: GET /api/jobs

**Change**: Default behaviour now excludes `archived` jobs.

| Param | Type | Notes |
|---|---|---|
| `status` | string (optional) | If omitted: excludes `archived`. Pass `archived` to show only archived. |
| All other params | unchanged | See existing contract |

**Response**: unchanged shape — `{ jobs: JobListing[], total: int }`

**Breaking change for frontend**: The "All" tab currently passes no `status` param, which will now implicitly exclude archived. This is the desired behaviour per spec (SC-001). The "All" tab label may be updated to "Active" in the UI to reflect this.

---

## Changed: PATCH /api/jobs/{id}/status

**Change**: Accepts two new `status` values in the request body.

```json
{ "status": "archived" }
{ "status": "shortlisted" }
```

Valid values (expanded): `saved`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`, `archived`, `shortlisted`

**Response**: unchanged — `{ id, status, transitioned_at }`

**Error**: 422 if transition is not permitted by the transition graph.

---

## New: POST /api/jobs/bulk-archive

Archives all `saved` jobs with `fit_score < 0.50` (display threshold: 50).

**Request body**: none

**Response**:
```json
{ "archived_count": 12 }
```

**Behaviour**:
- Only `saved` jobs are candidates (not `shortlisted`, not pipeline-stage jobs)
- Jobs without a `fit_score` (unscored) are excluded
- Each archived job gets a `status_transitions` record
- Returns count of jobs actually archived (may be 0)

---

## Frontend Type Changes

### `PipelineStatus` (types.ts)

Add `"archived"` and `"shortlisted"` to the union type.

### `VALID_STATUSES` set (jobs/page.tsx)

Add `"archived"` and `"shortlisted"` to the set.

### `STATUS_TABS` array (jobs/page.tsx)

Add tabs:
```typescript
{ value: "shortlisted", label: "Shortlisted" },
{ value: "archived",    label: "Archived" },
```

Rename the existing `"all"` tab label from "All" to "Active" (since it now excludes archived by default).

### `STATUS_CONFIG` (StatusBadge.tsx)

Add entries:
```typescript
archived:    { label: "Archived",    classes: "bg-gray-800 text-gray-500" },
shortlisted: { label: "Shortlisted", classes: "bg-amber-900 text-amber-200" },
```
