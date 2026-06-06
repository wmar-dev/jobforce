---
name: forge-tailor
description: Tailor your base resume to a specific job listing and optionally export a PDF. Fetches your base resume, reasons about tailoring here in Claude Code, posts the result to the backend, shows a diff of changes, then saves the PDF locally. Use when preparing a resume for a specific job application.
argument-hint: "<job_id>"
user-invocable: true
---

# Forge Tailor — Resume Tailoring Skill

Tailor your base resume to a specific job listing. All AI reasoning happens
here in Claude Code — no backend SDK calls are made.

## Usage

```
/forge-tailor <job_id>
```

## Steps

### Step 1: Validate backend is reachable

```
GET http://localhost:8000/api/jobs?limit=1
```

If this fails, print:

```
❌ Backend not reachable at http://localhost:8000 — run: cd backend && make dev
```

Then stop.

---

### Step 2: Fetch base resume, job listing, and tailoring instructions

```
GET http://localhost:8000/api/resume/base
GET http://localhost:8000/api/jobs/<job_id>
```

Also read `config/tailoring-instructions.md` from disk if it exists. This file
contains hard constraints and phrasing corrections that must be applied during
tailoring. If the file is absent, proceed without it.

If base resume returns 404:
```
❌ No base resume found. Add config/resume.json and restart the backend.
```

If job returns 404:
```
❌ Job #<job_id> not found.
```

Then stop in either case.

---

### Step 3: Ask clarifying questions

Before tailoring, reason about what you know and don't know about the candidate's
experience relative to this specific job. Identify up to 5 points where a short
answer would meaningfully improve the tailored output — ambiguities in scope,
impact, or technology use that the resume doesn't make clear.

Skip any point already answered in `config/tailoring-instructions.md` under
`## Clarifications`.

If there are questions to ask, present them like this and WAIT for the user to
respond before proceeding:

```
⚒️ A few quick questions before I tailor for <job title> at <company>:

1. <specific question about a bullet or claim>
2. <specific question>
...

Answer any you know — press Enter to skip the rest and tailor with what's here.
```

If `config/tailoring-instructions.md` already covers all relevant ambiguities,
skip this step and proceed directly to Step 4.

#### After the user responds

- Record each answered question as a new entry under `## Clarifications` in
  `config/tailoring-instructions.md`, using this format:

  ```markdown
  ### <Role or company context, e.g. "Data engineering roles">
  - <Concise rule derived from the answer, written as a constraint or fact>
  ```

- If `## Clarifications` doesn't exist in the file yet, append it after the
  last section. If the file doesn't exist, create it with just the
  `## Clarifications` section.
- Do NOT duplicate a clarification already present in the file.
- Unanswered questions are skipped — do not record them.

---

### Step 4: Tailor the resume

Using the base resume's `structured_data`, the job's `title` and `description`,
and any instructions from `config/tailoring-instructions.md` (including
clarifications just recorded), reason about which fields to adjust to better
match the role.

Rules:
1. ONLY adjust emphasis, keywords, and bullet phrasing
2. Do NOT add work history entries, companies, dates, or degrees that don't exist
3. Keep all factual information accurate — apply every hard constraint listed in
   tailoring-instructions.md before finalising any bullet
4. Return the full adjusted `structured_data` object

Produce the tailored version of the resume JSON in memory — do not write any files.

---

### Step 5: Save the tailored resume

```json
POST http://localhost:8000/api/resume/tailor
{
  "job_id": <job_id>,
  "structured_data": <tailored structured_data object>
}
```

The backend stores the result and returns the resume ID and a field-level diff.

---

### Step 6: Display diff summary

```
⚒️ Tailored Resume #<id> for Job #<job_id> — <job title>

Changes (<n> fields):
- summary: updated to highlight relevant experience
- work_history[0].bullets: adjusted emphasis on distributed systems
- skills: reordered to surface Python and FastAPI first
```

If no fields changed, print:
```
⚒️ Resume already well-matched — no changes needed.
```

---

### Step 7: Export to .tex and PDF

```
POST http://localhost:8000/api/resume/<tailored_id>/export
```

The response is JSON:
```json
{
  "tex_path": "/absolute/path/to/resume-company-title-YYYYMMDD-HHMMSS.tex",
  "pdf_path": "/absolute/path/to/resume-company-title-YYYYMMDD-HHMMSS.pdf"
}
```

Print the result:
```
✅ .tex written to: /absolute/path/to/resume-company-title-YYYYMMDD-HHMMSS.tex
✅ PDF written to:  /absolute/path/to/resume-company-title-YYYYMMDD-HHMMSS.pdf
```

If `pdf_path` is `null`:
```
✅ .tex written to: /absolute/path/to/resume-company-title-YYYYMMDD-HHMMSS.tex
⚠  PDF not generated — install texlive to compile PDFs (brew install --cask mactex)
```

## Notes

- Backend must be running: `cd backend && make dev`
- Base resume is loaded from `config/resume.json` on startup (see `config/resume.example.json`)
- Scores are not re-run automatically — run `/oracle-rank` after tailoring if you want updated fit scores
