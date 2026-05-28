# Oracle Rank — Job Fit Ranking Skill

Score all active job listings against your profile using Oracle's AI analysis.

## Usage

```
/oracle-rank [job_id ...]
```

Omit job IDs to rank all active (saved/applied/interviewing) listings.

## Steps

1. Call the Oracle ranking API:
   ```json
   POST http://localhost:8000/api/oracle/rank
   {
     "job_ids": [<id1>, <id2>]   // omit for all active
   }
   ```

2. Display results sorted by score descending:
   ```
   #1  Job #42 — Senior Backend Engineer @ Acme Corp
       Score: 87%  Confidence: high
       Rationale: Strong Python and FastAPI background matches core requirements.

   #2  Job #17 — Platform Engineer @ DevCo
       Score: 63%  Confidence: medium
       Rationale: Infrastructure experience relevant but missing Kubernetes specifics.
       ⚠ Job description is too sparse for reliable scoring
   ```

3. Report summary:
   - Total ranked
   - Score distribution (high/medium/low confidence counts)

## Notes

- Backend must be running: `cd backend && make dev`
- Set up your profile first via `PUT http://localhost:8000/api/profile` for accurate scoring
- Scores are cached — run again after updating your profile or editing descriptions
