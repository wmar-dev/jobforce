---
name: oracle-rank
description: Score and rank active job listings against your profile using AI reasoning. Fetches jobs from the backend, evaluates fit, writes scores back, and prints a ranked summary. Use when you want to see which jobs are the best match.
argument-hint: "[job_id ...]"
user-invocable: true
---

# Oracle Rank — Job Fit Ranking Skill

Score active job listings against your profile. All AI reasoning happens
here in Claude Code — no backend SDK calls are made.

## Usage

```
/oracle-rank [job_id ...]
```

Omit job IDs to rank all active (saved/applied/interviewing) listings.

## Steps

### Step 1: Validate backend is reachable

```
GET http://localhost:8000/api/jobs?limit=1
```

If this fails, print:

```
❌ Backend not reachable at http://localhost:8000 — run: cd backend && make dev
```

Then stop. Do not make any writes.

---

### Step 2: Fetch jobs to rank

If job IDs were provided as arguments (e.g., `/oracle-rank 2 5 7`):

```
GET http://localhost:8000/api/jobs/2
GET http://localhost:8000/api/jobs/5
GET http://localhost:8000/api/jobs/7
```

Fetch each by ID. Skip any that return 404.

If no job IDs were provided:

```
GET http://localhost:8000/api/jobs?limit=200
```

Filter the results to only jobs with `status` in: `saved`, `applied`, `interviewing`.

If no jobs are found, print:

```
🔮 No active jobs to rank. Capture some job listings via Scout first.
```

Then stop.

---

### Step 3: Fetch base resume

```
GET http://localhost:8000/api/resume/base
```

If this returns 404, note "No base resume configured" — scores will still
be produced but with `confidence: low`.

---

### Step 4: Score each job

For each job, reason about fit based on:

- **Candidate resume**: the structured JSON from `GET /api/resume/base`
- **Job listing**: title, location, role_type, description

Produce:

- `score`: float between 0.0 (no fit) and 1.0 (perfect fit)
  - Clamp to [0.0, 1.0] — never store out-of-range values
- `confidence`: one of "high", "medium", "low"
  - score ≥ 0.7 → "high"
  - score ≥ 0.4 → "medium"
  - score < 0.4 → "low"
  - If description is fewer than 100 characters → always "low" regardless of score
- `rationale`: 1–2 sentences explaining the score
- `warning` (optional): "Job description is too sparse for reliable scoring"
  if description < 100 chars

If no base resume is configured, score with `confidence: low` for all jobs and
note "No base resume found — add config/resume.json and restart the backend."

---

### Step 5: Write each score to the backend

For each job scored, immediately after scoring (do not batch):

```
PATCH http://localhost:8000/api/jobs/{job_id}
Content-Type: application/json

{
  "fit_score": <score>,
  "fit_scored": 1,
  "fit_confidence": "<confidence>",
  "fit_rationale": "<rationale>"
}
```

If the PATCH fails for a specific job, log the error and continue to the
next job. Do not abort the entire session.

---

### Step 6: Print ranked summary

Sort all successfully scored jobs by `score` descending and print:

```
🔮 Oracle Ranking Complete

#1  Job #2 — Software Engineer, Ad Formats @ OpenAI
    Score: 85%  Confidence: high
    Rationale: Strong systems engineering background aligns with ad infrastructure work.

#2  Job #5 — Platform Engineer @ DevCo
    Score: 42%  Confidence: medium
    Rationale: Infrastructure experience relevant but role focuses on Kubernetes expertise not present in profile.
    ⚠ Job description is too sparse for reliable scoring

──────────────────────────────────
Total ranked: 2  |  High: 1  |  Medium: 1  |  Low: 0
```

---

## Notes

- Backend must be running: `cd backend && make dev`
- Add your resume at `config/resume.json` (see `config/resume.example.json`) and restart for accurate scoring
- Scores are overwritten on each run — re-run after updating your resume
- The Oracle UI at http://localhost:3000/oracle displays stored scores from
  previously completed ranking sessions
