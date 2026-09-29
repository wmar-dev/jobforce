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
/oracle-rank [job_id ... | unscored]
```

- **No argument**: rank all active (saved/applied/interviewing) listings
- **`unscored`**: rank only active listings where `fit_scored` is falsy
- **Job IDs**: rank specific jobs by ID

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

If the argument is `unscored` (case-insensitive, with or without punctuation):

```
GET http://localhost:8000/api/jobs?limit=200&fit_scored=false
```

Filter to jobs with `status` in `saved`, `applied`, `interviewing`. If none, print:

```
🔮 No unscored jobs — all active listings already have fit scores.
```

Then stop.

If no argument was provided:

```
GET http://localhost:8000/api/jobs?limit=200&status=saved
GET http://localhost:8000/api/jobs?limit=200&status=applied
GET http://localhost:8000/api/jobs?limit=200&status=interviewing
```

Fetch all three status buckets separately (the default endpoint caps at 200 and excludes archived; fetching per-status avoids silently truncating). Merge and deduplicate by `id`.

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

Store the structured JSON. The `structured_data` field is returned as a **dict** (already parsed) — do NOT call `json.loads()` on it. If this returns 404, note "No base resume configured" — scores will still be produced but with `confidence: low`.

Also read `config/scouting-notes.md` from disk if it exists. If present, use its `## Scoring notes` section as additional context when reasoning about fit in Step 4 — it captures preferences the resume alone can't express (e.g. "don't penalize on-call requirements", "deprioritize people-management roles"). If the file is absent, or has no `## Scoring notes` section, proceed without it.

---

### Step 4: Score jobs

Score every job fetched in Step 2 against the resume — and against
`## Scoring notes` from `config/scouting-notes.md`, if present — producing
for each:

- `score`: float between 0.0 (no fit) and 1.0 (perfect fit), clamped to [0.0, 1.0]
- `confidence`:
  - score ≥ 0.7 → "high"
  - score ≥ 0.4 → "medium"
  - score < 0.4 → "low"
  - description < 100 chars → always "low" regardless of score
- `rationale`: 1–2 sentences explaining the score
- `warning` (optional): "Job description is too sparse for reliable scoring" if description < 100 chars

**If there are more than 15 jobs to score, delegate the scoring loop to
subagents instead of doing it inline.** Dumping dozens of full job
descriptions into this conversation doesn't go away once scoring finishes —
it stays in context and gets re-billed as cache-read on every later turn for
the rest of the session. A subagent's raw tool results never enter this
conversation; only what it explicitly returns does.

- Split the job ID list into chunks of ~40 jobs.
- Launch one `Agent` call per chunk (`subagent_type: general-purpose`, all
  issued in the same message so the chunks run in parallel;
  `run_in_background: false`, since Step 6 needs every chunk's results
  before it can print the ranked summary). Each prompt must be
  **self-contained** — the subagent has no access to this conversation —
  and include:
  - The base resume's summary, skills, and work history (from Step 3)
  - The `## Scoring notes` section from `config/scouting-notes.md`, if present
  - This chunk's list of job IDs
  - The scoring rubric above, plus: "For each job ID, `GET
    http://localhost:8000/api/jobs/{id}`, truncate `description` to 2000
    chars, score it, then immediately `PATCH` the score (see Step 5). Do not
    include full job descriptions in your final reply — return only a
    compact JSON array of `{id, title, company_name, score, confidence}`
    records."
- Merge the compact records returned by all chunks into one list for Step 6.

**If there are 15 or fewer jobs**, score them inline instead — the overhead
of a subagent isn't worth it for a small batch:

1. Process in batches of up to 5. For each job, load only `id`, `title`,
   `company_name`, `location`, `role_type`, `description` (first 2000 chars
   only — truncate longer descriptions).
2. Score each job per the rubric above.
3. Immediately PATCH each scored job (Step 5 below).
4. After writing all scores for the batch, **discard the job description
   text** — retain only the compact score record: `{id, title,
   company_name, score, confidence}`.
5. Print a one-line progress update: `Scored batch N/M (jobs X–Y)` then move
   to the next batch.

If no base resume is configured, score with `confidence: low` for all jobs and
note "No base resume found — add config/resume.json and restart the backend."

---

### Step 5: Write each score to the backend

For each job scored, immediately after scoring (do not wait for the full batch to finish):

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

After all batches are complete, sort all scored jobs by `score` descending using only the compact records retained from Step 4. Print:

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
- `config/scouting-notes.md` (optional, copy from `config/scouting-notes.example.md`) lets you add freeform scoring context under `## Scoring notes` that the resume alone can't capture
- Scores are overwritten on each run — re-run after updating your resume or scouting-notes.md
- The Oracle UI at http://localhost:3000/oracle displays stored scores from
  previously completed ranking sessions
