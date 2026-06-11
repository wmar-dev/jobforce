---
name: scout-reject
description: Mark a job application as rejected in Jobforce. Looks up the listing by company name, job title, or job ID, confirms the match, and transitions its status to "rejected" (recording the audit trail). Use whenever the user says they got rejected, received a rejection email/notice, or wants to mark an application as rejected/declined — including casual phrasing like "I got rejected by Acme" or "Acme passed on me".
argument-hint: "<company name, job title, or job ID>"
user-invocable: true
---

# Scout Reject

Mark a job listing as `rejected` and record the status transition.

## Usage

```
/scout-reject <company name, job title, or job ID>
```

## Step 1: Validate backend is reachable

```bash
curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/api/jobs?limit=1"
```

If the response is not `200`, stop and print:
```
❌ Backend not reachable at http://localhost:8000. Start it with: make dev
```

## Step 2: Resolve the target job

**If the argument is a bare integer**, treat it as a job ID directly:
```
GET http://localhost:8000/api/jobs/{id}
```
If 404, report "Job #{id} not found" and stop. Otherwise this is the target — skip to Step 3.

**Otherwise, treat the argument as a company name (or part of one):**

1. `GET http://localhost:8000/api/companies` and find companies whose `name` contains the argument, case-insensitive.
2. For each matching company, `GET http://localhost:8000/api/companies/{id}` and look at `listings`.
3. From those listings, keep only ones whose `status` is `saved`, `shortlisted`, `applied`, or `interviewing` — these are the only statuses that can transition to `rejected`. (`offer`/`rejected`/`withdrawn` are terminal.)
4. If no company name matches at all, fall back to a title search: `GET http://localhost:8000/api/jobs?limit=200&status=<saved|shortlisted|applied|interviewing>` (one call per status) and keep listings whose `title` contains the argument, case-insensitive.

**Narrow to one candidate:**

- **Zero candidates**: print `🤷 No active application found matching "<argument>" — it may already be rejected/archived, or hasn't been captured yet.` and stop.
- **One candidate**: that's the target.
- **Multiple candidates**: if exactly one has status `applied` or `interviewing`, use that (most likely "the application"). Otherwise list them as `#{id} — {company} — {title} ({status})` and ask the user which one to mark rejected.

## Step 3: Transition to rejected

```
PATCH http://localhost:8000/api/jobs/{id}/status
Content-Type: application/json

{"status": "rejected"}
```

- **200**: success.
- **422 / `INVALID_TRANSITION`**: the job is already in a terminal status (e.g. already `rejected`, `withdrawn`, or `offer`). Report the current status and that no change was made.
- **404**: report "Job #{id} not found".

## Step 4: Confirm

On success, print a short confirmation, e.g.:

```
✅ Marked "Senior ML/AI Engineer" at Acme Corp as rejected (was: applied).
```

Optionally add a brief, supportive one-liner — keep it short and don't dwell.
