# Research: Forge LaTeX & PDF Export per Job

**Branch**: `013-forge-tex-pdf` | **Date**: 2026-06-05

## Decision 1: Template rendering CLI — subprocess vs in-process

**Decision**: Invoke a thin `render_template.py` script as a subprocess (passing resume JSON via stdin or a temp file) rather than calling Jinja2 in-process.

**Rationale**: The spec and clarifications explicitly require CLI invocation for both the template render and the PDF compile steps. Using a subprocess also isolates template rendering from the FastAPI event loop and makes the render step independently testable as a CLI tool.

**Alternatives considered**:
- In-process Jinja2 (current implementation) — rejected per spec FR-010
- `jinja2-cli` third-party tool — rejected; adds a new dependency; `render_template.py` reuses existing Jinja2 installation with no extras

## Decision 2: `render_template.py` interface

**Decision**: `render_template.py` accepts the resume JSON path and output `.tex` path as positional CLI arguments: `python render_template.py <json_path> <tex_output_path>`. The script reads the JSON, renders the template, and writes the `.tex` file.

**Rationale**: Positional file paths are the simplest, most debuggable interface. Avoids stdin piping complexity. Both paths are known at call time.

**Alternatives considered**:
- stdin JSON + stdout tex — harder to debug, no file on disk mid-pipeline
- Environment variables — unconventional for file I/O

## Decision 3: Output directory creation

**Decision**: The backend service (`export_resume()`) creates `output/` at the project root on first use via `Path.mkdir(parents=True, exist_ok=True)`. The directory is gitignored.

**Rationale**: Matches clarification Q1 answer (Option A). Auto-creation avoids a separate setup step. `exist_ok=True` is idempotent.

**Alternatives considered**:
- Require user to create `output/` manually — poor UX
- Configurable path in `config.yaml` — deferred; not needed for v1

## Decision 4: Filename format

**Decision**: `resume-<company-slug>-<title-slug>-<YYYYMMDD-HHMMSS>.tex/.pdf`

- Company and title are slugified: lowercased, non-alphanumeric runs replaced with `-`, leading/trailing `-` stripped.
- Timestamp is the export time: `YYYYMMDD-HHMMSS`.
- Example: `resume-acme-corp-senior-software-engineer-20260605-143022.tex`

**Rationale**: Matches clarification Q3 answer (timestamp suffix). Unique per export. Human-readable. Company name included per user feedback.

**Alternatives considered**:
- Resume ID suffix — rejected per user correction
- Job ID only — not human-readable

## Decision 5: Special-character escaping for LaTeX

**Decision**: Add a `_escape_latex(value: str) -> str` helper in `render_template.py` (and register it as a Jinja2 filter) that escapes the 10 special LaTeX characters: `& % $ # _ { } ~ ^ \`.

**Rationale**: The existing template passes values directly into LaTeX without escaping. Any `&` or `_` in a company name or job title will break compilation. FR-006 and SC-005 require this. The helper is small (a single `str.replace` chain or regex), testable in isolation, and registered as a Jinja2 filter so every `\VAR{...}` call can opt in.

**Alternatives considered**:
- Escape at data-entry time — wrong layer; data should be stored clean
- Rely on LaTeX's `\detokenize` — less portable, harder to test

## Decision 6: Existing `render_pdf` and export endpoint migration

**Decision**: The existing `render_pdf()` function in `forge.py` is replaced by two new functions:
- `render_tex_cli(structured_data, output_dir, filename_stem) -> Path` — invokes `render_template.py` subprocess, returns `.tex` path
- `compile_pdf_cli(tex_path) -> Path` — invokes `latexmk`/`pdflatex`, returns `.pdf` path

The `POST /resume/{id}/export` endpoint is rewritten to call these, write both files to `output/`, and return a JSON body `{"tex_path": "...", "pdf_path": "..."}` rather than streaming bytes.

**Rationale**: Streaming bytes was designed for browser download, which the spec explicitly removes. Returning paths is simpler and consistent with the disk-write model.

**Alternatives considered**:
- Keep streaming endpoint, add a separate disk-write endpoint — two code paths for the same thing; rejected per simplicity principle
