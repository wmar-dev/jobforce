# Implementation Plan: Site Adapter Skill

**Branch**: `004-site-adapter-skill` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/004-site-adapter-skill/spec.md`

## Summary

Create a Claude Code skill (`/site-adapter-update <url>`) that uses the
Playwright MCP server to inspect any job posting page, extracts a structured
field summary, then generates or updates the site-specific adapter in
`chrome-extension/content.js`. The skill is a Markdown instruction file (no
compiled code, no SDK calls) that runs entirely within Claude Code's built-in
capabilities.

## Technical Context

**Language/Version**: JavaScript (ES2020, no transpilation) for the adapter
code written into `content.js`; Markdown + Claude Code skill DSL for the skill
file itself.

**Primary Dependencies**: Playwright MCP server (already configured via
`claude mcp add`); Claude Code slash-command skill loader; existing
`chrome-extension/content.js` adapter registry.

**Storage**: File-only — `chrome-extension/content.js` (modified in place);
`.claude/skills/site-adapter-update.md` (new skill file).

**Testing**: Manual end-to-end validation — run skill against a known URL,
load updated extension in Chrome, trigger capture, verify extracted fields.
No automated test suite for the skill file itself (Markdown instructions).
For the adapter JS code changes: existing Jest tests in
`chrome-extension/` cover the adapter registry and merge framework.

**Target Platform**: Claude Code CLI (macOS/Linux developer environment);
Chrome extension Manifest V3.

**Project Type**: Developer tooling / Claude Code skill + Chrome extension
adapter patch.

**Performance Goals**: Field summary returned in under 30 seconds (SC-001);
single skill invocation produces a working adapter (SC-002).

**Constraints**: No external AI SDK calls (Constitution Principle VI). No
modifications to any file if page navigation fails (FR-007). Must preserve
existing adapter registry structure verbatim (FR-005).

**Scale/Scope**: Single developer, local environment. One skill file, one
JS adapter object per hostname in one content script.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle                   | Status    | Notes                                                                                           |
| --------------------------- | --------- | ----------------------------------------------------------------------------------------------- |
| I. Test-First Development   | ✅ Pass   | Adapter JS changes covered by existing Jest suite; skill file is Markdown (no testable logic)   |
| II. Code Quality Standards  | ✅ Pass   | Adapter JS is simple extractors; complexity well under limit                                    |
| III. Self-Improvement Loop  | ✅ Pass   | Skill itself is the feedback loop artifact                                                      |
| IV. Simplicity & Clarity    | ✅ Pass   | Skill is a single Markdown file; no new abstractions                                            |
| V. Observability & Feedback | ✅ Pass   | Skill produces human-readable field summary before any write                                    |
| VI. Cost-Conscious AI Usage | ✅ Pass   | No SDK imports; all AI via Claude Code subscription                                             |

No violations. Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/004-site-adapter-skill/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── skill-contract.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
.claude/skills/
└── site-adapter-update.md   # NEW: the slash-command skill file

chrome-extension/
├── content.js               # MODIFIED: adapter added/updated per-run
└── content.test.js          # EXISTING: Jest tests (no new file needed)
```

**Structure Decision**: Tooling-only change. No new source directories.
The skill is a single Markdown file in `.claude/skills/`. The only runtime
artifact is the updated adapter entry in `content.js`.

## Complexity Tracking

> No violations — table not required.
