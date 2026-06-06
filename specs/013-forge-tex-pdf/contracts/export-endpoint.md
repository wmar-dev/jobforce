# Contract: POST /api/resume/{resume_id}/export

**Changed from**: streaming `application/pdf` response
**Changed to**: JSON response with file paths written to disk

## Request

```
POST /api/resume/{resume_id}/export
```

No request body.

| Path param  | Type | Description           |
|-------------|------|-----------------------|
| resume_id   | int  | ID of an existing Resume row |

## Response — 200 OK

```json
{
  "tex_path": "/absolute/path/to/output/resume-acme-senior-engineer-20260605-143022.tex",
  "pdf_path": "/absolute/path/to/output/resume-acme-senior-engineer-20260605-143022.pdf"
}
```

| Field     | Type         | Description                                              |
|-----------|--------------|----------------------------------------------------------|
| tex_path  | string       | Absolute path to the written `.tex` file                 |
| pdf_path  | string\|null | Absolute path to the written `.pdf`, or null if LaTeX unavailable |

## Response — 200 OK (LaTeX unavailable)

```json
{
  "tex_path": "/absolute/path/to/output/resume-acme-senior-engineer-20260605-143022.tex",
  "pdf_path": null
}
```

When LaTeX is unavailable, `pdf_path` is `null`. The `.tex` file is always written. HTTP status is still `200` — the `.tex` export succeeded.

## Response — 404 Not Found

```json
{ "detail": "Resume not found" }
```

## Response — 500 Internal Server Error

```json
{ "detail": "Template rendering failed: <reason>" }
```

Returned when `render_template.py` subprocess exits non-zero or the `.tex` file is not produced.

## Notes

- The previous `503 LATEX_UNAVAILABLE` response code is retired; `pdf_path: null` communicates unavailability without an error status.
- Files are written to the `output/` directory at the project root (auto-created).
- Filenames include company, title, and timestamp — guaranteed unique per export.
