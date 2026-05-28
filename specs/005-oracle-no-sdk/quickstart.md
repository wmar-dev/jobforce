# Quickstart: Oracle SDK-Free Job Ranking

**Feature**: `005-oracle-no-sdk` | **Date**: 2026-05-27

## Prerequisites

1. Backend running: `cd backend && make dev`
2. At least one active job listing with a description
3. User profile configured (optional but recommended):
   ```
   PUT http://localhost:8000/api/profile
   ```

## Rank jobs

```
/oracle-rank
```

Claude will:
1. Fetch all active jobs (saved/applied/interviewing) from the backend.
2. Fetch your user profile.
3. Score each job for fit (0.0–1.0), assign confidence, write a rationale.
4. Write each result back via `PATCH /api/jobs/{id}`.
5. Print a ranked summary.

To rank specific jobs only:

```
/oracle-rank 2 5 7
```

## View results

Open `http://localhost:3000/oracle` — previously ranked jobs display with
scores and rationale. The page no longer has a "Rank Jobs" button; use
`/oracle-rank` in Claude Code instead.

## Verify SDK is removed

```bash
grep -r "anthropic" backend/jobforce/
# Should return: no output
```

## Run backend tests

```bash
cd backend && make test
# All existing oracle contract tests should pass
```

## Troubleshooting

| Symptom | Fix |
| --- | --- |
| "backend not reachable" | Run `cd backend && make dev` first |
| Scores not appearing in UI | Check that `fit_scored=1` via `GET /api/jobs/{id}` |
| All scores 0.0 | User profile may be empty — set it via `PUT /api/profile` |
| `grep anthropic` finds results | Check `backend/jobforce/services/oracle.py` was saved |
