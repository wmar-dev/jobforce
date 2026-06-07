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

### Step 3: Ask clarifying questions (only if needed)

Reason about whether any ambiguity in the resume — relative to this specific job
— would materially change how a bullet is phrased or whether a claim can be made.
Default to **not asking**: if the existing instructions and resume are sufficient
to tailor accurately, skip this step entirely and proceed to Step 4.

Only surface a question when all three are true:
1. The answer would change a specific bullet or claim in a meaningful way
2. The answer cannot be inferred from the resume, the job description, or
   `config/tailoring-instructions.md`
3. The point has not already been addressed under `## Clarifications`

If any questions meet that bar, ask them (max 3) and WAIT for the user to respond:

```
⚒️ One quick question before I tailor for <job title> at <company>:

1. <specific question>

Skip with Enter to tailor with what's here.
```

#### After the user responds

- Record each answered question as a new entry under `## Clarifications` in
  `config/tailoring-instructions.md`:

  ```markdown
  ### <Role or company context>
  - <Concise constraint or fact derived from the answer>
  ```

- If `## Clarifications` doesn't exist yet, append it. If the file doesn't
  exist, create it with just that section.
- Do NOT duplicate anything already present.
- Unanswered/skipped questions are not recorded.

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
4. Every claim in a rewritten bullet or summary must be traceable to the source
   text. If you cannot point to a specific word, phrase, or fact in the original
   bullet or resume that supports the claim, remove it.
5. Return the full adjusted `structured_data` object

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
