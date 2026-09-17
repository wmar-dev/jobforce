---
name: forge-import
description: Parse a resume PDF or DOCX into config/resume.json's structured_data schema, merging with any existing personal info and flagging sections that need template support. Use when you have an updated resume file and want to refresh your Jobforce base profile.
argument-hint: "[path-to-resume-pdf-or-docx]"
user-invocable: true
---

# Forge Import — Resume PDF/DOCX → resume.json

Parse a resume file (PDF or DOCX) and write it into `config/resume.json`,
matching the schema documented in `config/resume.example.json`. All reasoning
happens here in Claude Code — no backend calls are required.

## Usage

```
/forge-import [path-to-resume-pdf-or-docx]
```

## Steps

### Step 1: Locate the source file

If a path was given as an argument, use it. Otherwise look for `*.pdf` and
`*.docx` files in the repository root. If exactly one match, use it. If
multiple, list them and ask the user which one. If none, stop and ask for a
path.

Reject any other extension — ask the user to convert it to PDF or DOCX first.

---

### Step 2: Read existing `config/resume.json` (if present)

```
Read config/resume.json
```

If it doesn't exist or contains only placeholder data (e.g. name "Bob Dev"),
treat it as empty — there's nothing to merge.

This existing data matters because the source file often **won't** contain
contact info (email, phone, links) that's already correct in `resume.json`.
Don't null those out just because the new file doesn't repeat them.

---

### Step 3: Read the source file

**PDF:**

```
Read <path-to-resume.pdf>
```

The Read tool returns the PDF's text content directly (multimodal).

**DOCX:** the Read tool doesn't parse `.docx`, so extract its text with
`python-docx` via an ephemeral `uv` run (no permanent dependency added to
`backend/pyproject.toml` — this only runs inside the skill):

```bash
uv run --with python-docx python3 -c "
import sys
from docx import Document

doc = Document(sys.argv[1])
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)

for table in doc.tables:
    for row in table.rows:
        cells = [c.text.strip() for c in row.cells]
        if any(cells):
            print(' | '.join(cells))
" <path-to-resume.docx>
```

Treat the printed output as the resume text for Step 4. This only captures
paragraphs and tables — if the resume puts content in headers/footers or text
boxes, note that to the user since it will be missed.

---

### Step 4: Map content to the schema

Build the `structured_data` object using `config/resume.example.json` as the
schema reference. Mapping rules:

| Resume section | JSON field | Rules |
| --- | --- | --- |
| Name (header) | `personal_info.name` | Required |
| Email | `personal_info.email` | **Required** by the LaTeX template. If the source file doesn't list one, keep the existing `resume.json` value. If neither has one, ask the user. |
| Phone / Location / LinkedIn / GitHub / Website | `personal_info.*` | Optional. If the source file doesn't include one, **preserve the existing value** rather than nulling it. |
| Summary / Objective / Profile | `summary` | `null` if absent. Don't invent one. |
| Experience / Work History / Employment | `work_history[]` | See date and bullet rules below. |
| Education | `education[]` | `degree`, `institution`, `end_date` = graduation year (string), `gpa` if shown, else `null`. |
| Skills / Technical Skills (incl. sub-categories like Languages, Frameworks, Tools) | `skills[]` | Flatten **all** categories into a single array, preserving the original order. Don't dedupe across categories unless there's an exact duplicate. |
| Certifications | `certifications[]` | `{name, issuer, year}`. |
| Projects | `projects[]` | `{name, url, description, bullets}`. |

**Date formatting:**
- `"Month YYYY"` → `"YYYY-MM"` (e.g. "October 2016" → `"2016-10"`)
- `"Present"` / "Current" / blank end date → `end_date: null` (the template
  renders this as "Present")
- Education with only a graduation year → `end_date: "YYYY"`, `start_date: null`

**Bullets:** copy verbatim — don't rephrase, summarize, or fix wording. This
is the canonical base resume; tailoring/rewriting happens in `/forge-tailor`,
not here.

---

### Step 5: Handle sections outside the core schema

Resumes often have sections the schema doesn't model: Coursework, Patents,
Publications, Awards, Languages, Volunteer work, etc.

**Don't drop this content.** `structured_data` is stored as `dict[str, Any]`
end-to-end (SQLAlchemy column is untyped JSON text, backend routers type it
`Any`) — Oracle ranking and Forge's diff both handle arbitrary top-level keys
automatically. Add a new top-level field using a `snake_case` name derived
from the section heading:

- **Coursework** → `coursework: string[]`. If the source is a comma-separated
  run-on line (common when courses themselves contain colons, e.g.
  `"Provider: Course Name, Other Course (ABC)"`), split on top-level commas
  into separate entries — each entry can itself contain a colon.
- **Patents** → `patents: {title, number}[]`, parsed from patterns like
  `"Attribute extraction US-10445812-B2"` → `{"title": "Attribute extraction", "number": "US-10445812-B2"}`.
- Other sections (Publications, Awards, Languages, ...) → `string[]` of the
  raw line items unless the structure clearly maps to objects.

These extension fields **will not render** in the generated PDF until
`backend/jobforce/templates/resume.tex.j2` (and optionally
`frontend/src/lib/types.ts`'s `ResumeStructuredData`) are extended with a
matching section. Note this in the Step 7 summary — don't silently extend the
template without asking.

---

### Step 6: Merge and write

- Start from the existing `resume.json` (Step 2), then overlay everything
  parsed from the source file.
- For `personal_info`, merge field-by-field per the rules in Step 4 (source
  file wins if present, otherwise keep existing).
- For list fields (`work_history`, `education`, `skills`, extension fields),
  **replace wholesale** with the source file's content — it is the source of
  truth for resume content, contact info is the exception.
- Back up the previous file first: `cp config/resume.json config/resume.json.bak`
  (skip if it didn't exist or was placeholder data).
- Write the merged object to `config/resume.json`.
- Validate: `python3 -m json.tool config/resume.json > /dev/null && echo "valid JSON"`.

---

### Step 7: Summarize

Print a short summary in this style:

```
✅ config/resume.json updated from <source filename>

- personal_info: kept existing email/phone/location, name updated
- work_history: 4 entries (Meta, Google, BloomReach, Manoharan Lab)
- education: 2 entries
- skills: 21 entries
- New extension fields not yet rendered by resume.tex.j2: coursework (4), patents (1)

Backup of previous file: config/resume.json.bak
```

If extension fields were added, ask whether to extend `resume.tex.j2` (and
`ResumeStructuredData` in `frontend/src/lib/types.ts`) to render them as new
sections — do this only if the user confirms.

---

## Notes

- This skill only writes `config/resume.json`. To apply it to the running
  app: `cd backend && uv run python -m jobforce.db.seed` (re-seeds the base
  resume), then `/oracle-rank` to refresh fit scores against the new profile.
- `config/resume.json` is gitignored — there's no git history to fall back on,
  hence the `.bak` copy in Step 6.
