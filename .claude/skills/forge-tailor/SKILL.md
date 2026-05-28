---
name: forge-tailor
description: Tailor your base resume to a specific job listing and optionally export a PDF. Fetches your base resume, posts to the tailor endpoint, shows a diff of changes, then saves the PDF locally. Use when preparing a resume for a specific job application.
argument-hint: "<job_id>"
user-invocable: true
---

# Forge Tailor — Resume Tailoring Skill

Tailor your base resume to a specific job listing and download the PDF.

## Usage

```
/forge-tailor <job_id>
```

## Steps

1. Fetch the base resume:
   ```
   GET http://localhost:8000/api/resume/base
   ```
   If 404: "No base resume found. Upload via PUT /api/resume/base first."

2. POST to tailor endpoint:
   ```json
   POST http://localhost:8000/api/resume/tailor
   {
     "job_id": <job_id>,
     "base_resume_id": <base_id>
   }
   ```

3. Display diff summary:
   ```
   ⚒️ Tailored Resume #<id> for Job #<job_id>
   
   Changes (3 fields):
   - skills: added "FastAPI", "SQLAlchemy"
   - work_history[0].bullets: adjusted emphasis
   - summary: updated to highlight relevant experience
   ```

4. Export PDF (optional):
   ```
   POST http://localhost:8000/api/resume/<tailored_id>/export
   ```
   Save to `./resume_job_<job_id>.pdf`
   - **200**: "✅ PDF saved to ./resume_job_<job_id>.pdf"
   - **503**: "LaTeX not installed — install texlive to generate PDFs"

## Notes

- Backend must be running: `cd backend && make dev`
- Base resume must be uploaded via the Forge UI or PUT /api/resume/base before running
