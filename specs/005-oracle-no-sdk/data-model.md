# Data Model: Oracle SDK-Free Job Ranking

**Feature**: `005-oracle-no-sdk` | **Date**: 2026-05-27

## Entities (unchanged DB schema)

No schema migrations required. All existing columns on `job_listings` are reused.

### JobListing (relevant fields)

| Field | Type | Description |
| --- | --- | --- |
| fit_score | float (0.0–1.0) | Computed fit score; null until ranked |
| fit_scored | int (0/1) | Boolean flag: 1 once scored |
| fit_confidence | text | "high", "medium", or "low" |
| fit_rationale | text | 1–2 sentence explanation from Claude |

### FitScore (runtime value, not persisted separately)

Produced by the skill per job, then written to `job_listings` via PATCH.

| Field | Type | Constraints |
| --- | --- | --- |
| score | float | 0.0 ≤ score ≤ 1.0; clamped by skill |
| confidence | string | one of: "high", "medium", "low" |
| rationale | string | 1–2 sentences; non-empty |
| warning | string or null | present when description is sparse (<100 chars) |

### Confidence derivation rule (unchanged from current code)

```
score >= 0.7  →  "high"
score >= 0.4  →  "medium"
score <  0.4  →  "low"
sparse desc   →  always "low" regardless of score
```

## State Transitions

```
job_listings.fit_scored = 0  (unranked)
  └─► skill calls PATCH /api/jobs/{id} with fit fields
        └─► job_listings.fit_scored = 1  (ranked)
              └─► skill run again → same transition (idempotent overwrite)
```

Re-running `/oracle-rank` always overwrites existing scores. There is no
"unrank" state — scores persist until overwritten or the job is deleted.
