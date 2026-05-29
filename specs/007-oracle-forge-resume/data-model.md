# Data Model: Oracle and Forge Use Resume as Candidate Profile

**Branch**: `007-oracle-forge-resume` | **Date**: 2026-05-28

## Removed Entity

### UserProfile (deleted)

Previously stored sparse free-text candidate fields. Removed in this feature. The `user_profiles` table remains in SQLite until a migration drops it, but the SQLAlchemy model and all application references are gone.

## Unchanged Entity (now primary candidate source)

### Resume

| Field | Type | Notes |
| ----- | ---- | ----- |
| id | Integer PK | Auto-increment |
| label | Text | e.g. "Base Resume", "Tailored for {title}" |
| is_base | Integer | `1` = canonical base resume, `0` = tailored copy |
| job_listing_id | Integer FK (nullable) | Null for base; set for tailored copies |
| structured_data | Text (JSON) | Full resume as JSON string |
| latex_source | Text (nullable) | LaTeX source for PDF rendering |
| pdf_path | Text (nullable) | Path to rendered PDF |
| created_at | Text (ISO8601) | Set on insert |
| updated_at | Text (ISO8601) | Updated on change |

**Invariant**: At most one row with `is_base=1` at any time. Enforced by application logic (seed and PUT /resume/base both upsert rather than insert).

**structured_data shape** (defined by `config/resume.json` / `config/resume.example.json`):

```json
{
  "name": "string",
  "contact": { "email": "...", "phone": "...", "location": "..." },
  "summary": "string",
  "skills": ["..."],
  "experience": [
    {
      "company": "string",
      "title": "string",
      "dates": "string",
      "bullets": ["..."]
    }
  ],
  "education": [
    { "institution": "string", "degree": "string", "year": "string" }
  ]
}
```

Shape is flexible (additional keys allowed); oracle and forge consume it as opaque JSON passed to the AI prompt.

## Seed Behavior

`_seed_base_resume()` in `backend/jobforce/db/seed.py`:
- Reads `config/resume.json` at startup
- Skips if file missing (logs warning)
- Skips if a base resume row already exists (idempotent)
- Inserts `Resume(label="Base Resume", is_base=1, structured_data=...)`
