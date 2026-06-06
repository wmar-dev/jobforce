# Implementation Plan: Forge LaTeX & PDF Export per Job

**Branch**: `013-forge-tex-pdf` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/013-forge-tex-pdf/spec.md`

## Summary

Replace the in-process Jinja2 + LaTeX rendering in `forge.py` with a two-step CLI pipeline: (1) a `render_template.py` subprocess that merges `resume.tex.j2` with structured resume data to produce a `.tex` file, and (2) `latexmk`/`pdflatex` invoked as a subprocess to compile the `.tex` to PDF. Both artifacts are written to an `output/` directory in the project root. The forge-tailor skill is updated to invoke this pipeline and report the output paths. The backend export endpoint (`POST /resume/{id}/export`) is rewritten to write files to disk and return paths rather than stream bytes. A thin `render_template.py` CLI script is introduced to own template rendering.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript/Next.js 15 (frontend)

**Primary Dependencies**: FastAPI, SQLAlchemy (async), Jinja2, uv — existing stack; no new dependencies added

**Storage**: SQLite via SQLAlchemy; exported `.tex` and `.pdf` files written to `output/` on local filesystem; not stored in DB

**Testing**: pytest with pytest-cov; existing `make check` gate

**Target Platform**: macOS / Linux local developer machine (single-user tool)

**Project Type**: Web service (backend) + CLI skill

**Performance Goals**: PDF written to disk in under 30 seconds per SC-001

**Constraints**: No new Python packages; LaTeX is optional (graceful degradation); no in-process Jinja2 or LaTeX library calls for the export path; no `anthropic` SDK imports (Constitution VI)

**Scale/Scope**: Single user; no concurrency requirements beyond independent requests not corrupting each other

## Constitution Check

| Principle             | Status   | Notes                                                                  |
|-----------------------|----------|------------------------------------------------------------------------|
| I. Test-First         | ✅ PASS  | Tests written before implementation in each task                       |
| II. Code Quality      | ✅ PASS  | ruff + mypy strict enforced via `make check`                           |
| III. Self-Improvement | ✅ PASS  | `make check` runs all gates locally                                    |
| IV. Simplicity        | ✅ PASS  | CLI subprocess replaces in-process rendering — no new abstractions     |
| V. Observability      | ✅ PASS  | Structured logging on render/compile steps                             |
| VI. Cost-Conscious AI | ✅ PASS  | No Anthropic SDK imports; skill uses Claude Code subscription only     |

**Gate result**: All pass. No violations to justify.

## Project Structure

### Documentation (this feature)

```text
specs/013-forge-tex-pdf/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code Changes

```text
backend/
├── jobforce/
│   ├── services/
│   │   └── forge.py              # rewrite: remove in-process Jinja2/render_pdf; add render_tex_cli(), compile_pdf_cli(), export_resume()
│   ├── routers/
│   │   └── forge.py              # update: POST /{id}/export returns ExportOut (paths) not StreamingResponse; remove StreamingResponse import
│   └── scripts/
│       └── render_template.py    # new: CLI script — takes <json_path> <tex_output_path>, applies latex_escape filter, writes .tex
├── tests/
│   ├── contract/
│   │   └── test_forge.py         # update: export endpoint now returns JSON {tex_path, pdf_path}, not PDF bytes; remove 503 test; add null pdf_path test
│   └── integration/
│       └── test_forge_service.py # update: test render_tex_cli(), compile_pdf_cli(), export_resume(), latex_escape(); add special-char tests
output/                           # new: gitignored directory; created at runtime

frontend/
└── src/
    ├── components/forge/
    │   └── PDFDownloadButton.tsx  # replace: no longer downloads bytes; shows tex_path and pdf_path returned from export; rename to ExportButton.tsx
    └── app/forge/
        └── page.tsx               # update: wire ExportButton; display returned file paths instead of triggering browser download

.claude/skills/forge-tailor/
└── SKILL.md                       # update: Step 6 — remove HTTP export call; call POST /api/resume/{id}/export, read tex_path/pdf_path from response, print both paths to user
```

### forge-tailor skill changes (Step 6 detail)

Current Step 6 in `SKILL.md` calls `POST /api/resume/<id>/export`, saves a blob to `./resume_job_<job_id>.pdf`, and shows a success/failure message. The updated step:

1. Calls `POST /api/resume/<id>/export` (same endpoint, now returns JSON).
2. Reads `tex_path` and `pdf_path` from the response body.
3. Prints both paths:

   ```text
   ✅ Exported to:
      .tex → /path/to/output/resume-acme-senior-engineer-20260605-143022.tex
      .pdf → /path/to/output/resume-acme-senior-engineer-20260605-143022.pdf
   ```

4. If `pdf_path` is null, prints:

   ```text
   ✅ .tex exported to /path/to/output/resume-acme-senior-engineer-20260605-143022.tex
   ⚠  PDF skipped — LaTeX not installed (install texlive to enable PDF rendering)
   ```

### Forge UI changes (detail)

Current `PDFDownloadButton.tsx` fetches a blob via `POST /api/resume/{id}/export` and creates a browser download link. The updated component (`ExportButton.tsx`):

1. Calls `POST /api/resume/{id}/export` (JSON response).
2. Displays the returned `tex_path` and `pdf_path` as read-only text — no download link.
3. If `pdf_path` is null, shows the "LaTeX unavailable" note alongside the `.tex` path.
4. `api.ts`: `exportResumePdf()` renamed to `exportResume()`, return type changes from `Blob` to `{ tex_path: string; pdf_path: string | null }`.
5. `forge/page.tsx`: replaces `<PDFDownloadButton>` with `<ExportButton>`; shows export result panel below the diff.

## Phase 0: Research

See [research.md](research.md).

## Phase 1: Design

See [data-model.md](data-model.md) and [contracts/](contracts/).

## Complexity Tracking

*No constitution violations to justify.*
