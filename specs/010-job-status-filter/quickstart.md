# Quickstart: Job Status Filtering & Triage

## Prerequisites

- Backend running: `cd backend && make dev`
- Frontend running: `cd frontend && npm run dev`
- Existing DB with jobs (run `make seed` if needed)

## Run the DB migration

```bash
sqlite3 backend/data/jobforce.db < backend/jobforce/db/migrations/010_add_triage_statuses.sql
```

Verify: `sqlite3 backend/data/jobforce.db "SELECT name FROM sqlite_master WHERE type='table' AND name='job_listings';"` — should return `job_listings`.

## Test the new statuses

```bash
# Archive a job (replace 1 with a real job id in 'saved' status)
curl -X PATCH http://localhost:8000/api/jobs/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "archived"}'

# Shortlist a job
curl -X PATCH http://localhost:8000/api/jobs/2/status \
  -H "Content-Type: application/json" \
  -d '{"status": "shortlisted"}'

# Restore an archived job
curl -X PATCH http://localhost:8000/api/jobs/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "saved"}'

# Bulk archive low-score jobs
curl -X POST http://localhost:8000/api/jobs/bulk-archive

# Confirm archived jobs are excluded from default list
curl http://localhost:8000/api/jobs | jq '[.jobs[].status] | unique'
# Should NOT include "archived"

# Confirm archived jobs appear when explicitly requested
curl "http://localhost:8000/api/jobs?status=archived" | jq '.total'
```

## Verify Coach page includes shortlisted jobs

Navigate to `http://localhost:3000/coach` — shortlisted jobs should appear in the job selector alongside applied and interviewing jobs.

## Run quality gates

```bash
cd backend && make check
cd frontend && npm run lint && npm test
```
