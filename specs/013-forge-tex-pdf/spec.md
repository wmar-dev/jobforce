# Feature Specification: Forge LaTeX & PDF Export per Job

**Feature Branch**: `013-forge-tex-pdf`

**Created**: 2026-06-05

**Status**: Implemented

**Input**: User description: "Enable forge to take a resume and generate a tex file and a rendered pdf tailored for each specific job."

## Clarifications

### Session 2026-06-05

- Q: Where should exported files be written? → A: Fixed `output/` directory in the project root (auto-created if absent).
- Q: Which CLI tool renders the `.tex.j2` template to `.tex`? → A: A thin Python script (`render_template.py`) invoked as a subprocess.
- Q: How should filename collisions be handled when two resumes share the same company and job title? → A: Append a timestamp suffix (e.g., `resume-acme-senior-engineer-20260605-143022.pdf`).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Tailored Resume to Disk via Skill (Priority: P1)

A user runs the forge-tailor skill for a specific job. At the end of the run, the skill writes both a `.tex` file and a rendered PDF to the local filesystem and reports their paths — so the user can open, share, or submit the files immediately without any additional steps.

**Why this priority**: Writing files to disk is the primary delivery mechanism for this feature. It makes tailored resumes immediately usable from the CLI without requiring any UI interaction.

**Independent Test**: Can be fully tested by running `/forge-tailor <job_id>` and verifying that a `.tex` file and a PDF are written to disk at the reported paths, and that the PDF contains the tailored resume content.

**Acceptance Scenarios**:

1. **Given** the forge-tailor skill completes successfully and LaTeX is available, **When** the skill finishes, **Then** both a `.tex` file and a PDF are written to disk and their paths are printed to the user.
2. **Given** the forge-tailor skill completes successfully and LaTeX is not available, **When** the skill finishes, **Then** only the `.tex` file is written to disk, the path is printed, and the user is told PDF rendering was skipped.
3. **Given** the exported files, **When** a user opens the PDF, **Then** it contains all resume sections populated from the tailored structured data with no missing or garbled content.

---

### User Story 2 - Export Any Resume to Disk via the Forge UI (Priority: P2)

A user is in the Forge web UI and wants to export a tailored (or base) resume. They click an "Export" button; the backend writes the `.tex` file and PDF to disk on the server and returns the file paths so the user knows where to find them.

**Why this priority**: The UI path is the complement to the skill path, letting users trigger exports without the CLI.

**Independent Test**: Can be fully tested by clicking "Export" in the Forge UI for a tailored resume and confirming the reported file paths exist on disk with correct content.

**Acceptance Scenarios**:

1. **Given** a tailored resume is displayed in the Forge UI, **When** the user clicks "Export", **Then** the backend writes both `.tex` and PDF to disk and the UI shows the resulting file paths.
2. **Given** an export is triggered from the UI and LaTeX is unavailable, **When** the backend processes the request, **Then** only the `.tex` file is written and the UI shows a clear message that PDF rendering is unavailable.
3. **Given** a base resume (not yet tailored), **When** the user triggers an export, **Then** the base resume is also exportable to `.tex` and PDF via the same mechanism.

---

### User Story 3 - Meaningful Filenames per Job (Priority: P3)

Exported files are named in a way that clearly identifies which job they were tailored for, so a user managing multiple applications can find the right file without opening each one.

**Why this priority**: Usability improvement — file naming is a quality-of-life concern that doesn't block the core export functionality.

**Independent Test**: Can be tested by exporting resumes for two different jobs and confirming the output filenames are distinct and include identifiable job information.

**Acceptance Scenarios**:

1. **Given** a resume tailored for a specific job, **When** the files are written to disk, **Then** the filenames include a sanitized combination of the company name, job title, and a timestamp (e.g., `resume-acme-senior-engineer-20260605-143022.tex`, `resume-acme-senior-engineer-20260605-143022.pdf`).
2. **Given** two resumes tailored for the same company and job title, **When** both are exported, **Then** their filenames do not collide because the timestamp suffix differs.

---

### Edge Cases

- What happens when a resume has no content in an optional section (e.g., no certifications, no projects)? Those sections should be omitted from the output rather than rendering empty.
- What happens when the resume contains special characters (ampersands, percent signs, underscores) in job titles or company names? These must be escaped correctly for LaTeX.
- What happens when the LaTeX CLI times out during compilation? The user should see a clear error message, and the `.tex` file written to disk should still be accessible for manual compilation.
- What happens when the user requests a PDF for a resume that no longer exists? A clear "not found" response with no partial files left on disk.
- What happens when two export requests for the same resume overlap? Each should complete independently without corrupting the other.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST render the LaTeX (`.tex`) source file by invoking `render_template.py` as a subprocess with the resume's structured data, writing the resulting `.tex` file to the `output/` directory.
- **FR-002**: The forge-tailor skill MUST invoke the system's LaTeX CLI toolchain (`latexmk` or `pdflatex`) to render the `.tex` file to PDF when the toolchain is available; the resulting PDF MUST be written to disk alongside the `.tex` file.
- **FR-003**: The forge-tailor skill MUST write both the `.tex` file and the PDF to the local filesystem and report both paths to the user upon successful completion.
- **FR-004**: When LaTeX is not available, the skill MUST still write the `.tex` file to disk, report its path, and clearly inform the user that PDF rendering was skipped.
- **FR-005**: The Forge UI MUST provide an "Export" action for any resume (base or tailored) that triggers the backend to write `.tex` and PDF files to the `output/` directory in the project root and return the resulting file paths.
- **FR-006**: Special characters in resume content (e.g., `&`, `%`, `_`, `#`, `$`, `^`, `{`, `}`, `~`, `\`) MUST be escaped correctly so the generated `.tex` compiles without errors.
- **FR-007**: The system MUST surface a clear error when PDF rendering is requested but LaTeX is unavailable, while still making the `.tex` file accessible.
- **FR-008**: Each exported file MUST be named using a sanitized combination of the company name, job title, and a timestamp to guarantee uniqueness (e.g., `resume-acme-senior-engineer-20260605-143022.tex`, `resume-acme-senior-engineer-20260605-143022.pdf`).
- **FR-009**: The system MUST NOT leave temporary compilation artifacts on disk after export completes or fails.
- **FR-010**: Both template rendering (`.tex.j2` → `.tex`) and PDF compilation (`.tex` → `.pdf`) MUST be performed by invoking CLI tools directly — not via in-process library calls or browser-download mechanisms.

### Key Entities

- **Resume**: Structured resume data (base or tailored). Key attributes: id, is_base flag, job_listing_id, structured_data (JSON). A tailored resume is linked to one job listing.
- **LaTeX Source**: A `.tex` file rendered from a resume's structured data. Derived artifact; always written to the local filesystem. Not stored in the database.
- **PDF**: A PDF produced by invoking the LaTeX CLI (`latexmk` or `pdflatex`) on the `.tex` source. Always written to the local filesystem alongside the `.tex` file.
- **Template Renderer**: A thin Python script (`render_template.py`) invoked as a subprocess to merge the resume template (`.tex.j2`) with structured resume data and write the `.tex` file to disk. Keeps template rendering out of the main application process.
- **Job Listing**: The job a resume was tailored for. Used to name exported files and provide context.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A tailored resume PDF is written to disk in under 30 seconds from triggering the export (via skill or UI).
- **SC-002**: 100% of generated `.tex` files compile without errors when tested against a standard LaTeX installation.
- **SC-003**: All resume sections present in the structured data appear in the exported PDF; no data is silently dropped.
- **SC-004**: The forge-tailor skill completes with both `.tex` and PDF artifacts reported in a single run, with no additional manual steps required from the user.
- **SC-005**: Special characters in resume content do not cause compilation failures in 100% of test cases with representative data.

## Assumptions

- LaTeX is an optional server-side dependency; the system degrades gracefully when it is absent.
- The existing `resume.tex.j2` template is the canonical template and will be extended (not replaced) to support this feature.
- Both the skill and the backend write exported files to the `output/` directory in the project root, which is created automatically if it does not exist.
- Template rendering (`.tex.j2` → `.tex`) is performed by invoking `render_template.py` as a subprocess; PDF compilation (`.tex` → `.pdf`) is performed by invoking `latexmk` or `pdflatex` — no in-process Jinja2 rendering or LaTeX library calls.
- Resume structured data is well-formed JSON conforming to the existing schema; malformed data is out of scope for this feature.
- The base resume can also be exported as `.tex`/PDF, not only tailored resumes.
- Concurrent export requests are handled independently; no locking or queuing mechanism is required given the single-user nature of this tool.
