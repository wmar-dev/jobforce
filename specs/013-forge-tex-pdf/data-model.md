# Data Model: Forge LaTeX & PDF Export per Job

**Branch**: `013-forge-tex-pdf` | **Date**: 2026-06-05

## Existing entities (unchanged)

### Resume (DB table)

No schema changes. Existing fields:

| Field             | Type       | Notes                                              |
|-------------------|------------|----------------------------------------------------|
| id                | int PK     | Auto-increment                                     |
| label             | str        | Human-readable name                                |
| is_base           | int (0/1)  | 1 = canonical base resume                          |
| job_listing_id    | int FK     | NULL for base resume                               |
| structured_data   | str (JSON) | Full resume as JSON string                         |
| latex_source      | str\|None  | Unused — not populated by this feature             |
| pdf_path          | str\|None  | Unused — not populated by this feature             |
| created_at        | str        | ISO timestamp                                      |
| updated_at        | str        | ISO timestamp                                      |

### JobListing (DB table)

No schema changes. Fields used by this feature: `id`, `title`, `company`.

## New: ExportResult (in-memory / response only)

Not persisted to the database. Returned by `export_resume()` and the export endpoint.

| Field     | Type | Notes                                                    |
|-----------|------|----------------------------------------------------------|
| tex_path  | Path | Absolute path to written `.tex` file                     |
| pdf_path  | Path\|None | Absolute path to written `.pdf`, or None if LaTeX unavailable |

## New: output/ directory (filesystem)

| Path pattern | Contents |
|---|---|
| `output/resume-<company>-<title>-<YYYYMMDD-HHMMSS>.tex` | Rendered LaTeX source |
| `output/resume-<company>-<title>-<YYYYMMDD-HHMMSS>.pdf` | Compiled PDF |

- Created automatically on first export.
- Gitignored.
- Files are never deleted by the application (user manages retention).

## New: render_template.py (CLI script)

**Location**: `backend/jobforce/scripts/render_template.py`

**Interface**:
```
python render_template.py <json_input_path> <tex_output_path>
```

| Argument         | Description                                      |
|------------------|--------------------------------------------------|
| json_input_path  | Path to a JSON file containing `structured_data` |
| tex_output_path  | Path where the rendered `.tex` file is written   |

**Exit codes**:
- `0` — success
- `1` — missing argument, unreadable input, template error, or write failure

**Jinja2 filter added**: `latex_escape` — escapes the 10 LaTeX special characters in any string value before interpolation.

## State transitions

No new state transitions. Export is a stateless read operation on an existing Resume record; it produces filesystem artifacts but does not mutate DB state.
