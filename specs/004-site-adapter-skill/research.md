# Research: Site Adapter Skill

**Feature**: `004-site-adapter-skill` | **Date**: 2026-05-27

## Decision Log

### 1. Skill format: Markdown instruction file vs. compiled script

**Decision**: Markdown instruction file (`.claude/skills/site-adapter-update.md`)

**Rationale**: All existing project skills (`scout-crawl.md`, `forge-tailor.md`,
etc.) are Markdown files that Claude Code interprets at runtime. This is the
established pattern in this project. No compilation, no runtime dependencies,
no SDK calls.

**Alternatives considered**:
- Python/shell script: requires execution permissions, cannot use Playwright MCP
  natively, adds a process boundary.
- Node.js script: adds a dependency, still can't call Playwright MCP directly.

---

### 2. Playwright MCP interaction strategy

**Decision**: Use `mcp__playwright__browser_navigate` + `mcp__playwright__browser_snapshot`
to capture the accessibility tree, then extract field values from the snapshot.

**Rationale**: The accessibility snapshot (YAML tree) provides structured,
labelled elements that are far easier to reason about than raw HTML. The
snapshot was confirmed against the live OpenAI careers page — all fields
(title in `heading[level=2]`, department+location in `paragraph` below the
heading, description in `paragraph` blocks under `strong` labels, compensation
in a sidebar `paragraph`) are cleanly visible in the tree.

**Alternatives considered**:
- Raw HTML via `browser_evaluate`: harder to parse, brittle to style changes.
- `browser_take_screenshot`: visual only, cannot extract text programmatically.

---

### 3. Adapter selector strategy for OpenAI careers pages

**Decision**: Use targeted CSS selectors derived from the live page structure,
not brittle nth-child positional selectors.

From the Playwright snapshot of `openai.com/careers/software-engineer-ad-formats-san-francisco/`:

| Field        | DOM location                                    | Selector                                  |
| ------------ | ----------------------------------------------- | ----------------------------------------- |
| title        | `heading[level=2]` inside `main`                | `main h2`                                 |
| location     | `paragraph` containing "– [City]" text          | `main h2 + p` (text after ` - `)          |
| description  | All `paragraph` elements inside `main article`  | `main > div > div` (scrollable body)      |
| compensation | Sidebar `paragraph` with `strong` "Compensation"| `[aria-label*="Compensation"] p`, fallback to text scan |

Existing `openaiAdapter.location` uses `h1 + p` — the live page shows the job
title is an `h2`, not `h1`. This is a confirmed regression to fix.

**Rationale**: Semantic selectors (heading level, sibling relationships) survive
minor layout refactors better than class-name or nth-child selectors.

---

### 4. Content script modification strategy

**Decision**: The skill reads `content.js`, locates the `ADAPTERS` object
literal, and surgically replaces or inserts the named adapter entry.
The rest of the file (generic adapter, `runAdapter`, `merge`,
message listener, exports) is left entirely unchanged.

**Rationale**: The existing file structure is well-defined and has a clear
insertion point (`const ADAPTERS = { ... }`). Surgical edit preserves all
existing adapters and the merge framework, satisfying FR-005 and FR-006.

**Alternatives considered**:
- Rewrite entire file: high risk of regression, violates FR-005.
- Separate adapter registry file: requires changes to `content.js` import
  structure — out of scope for this feature.

---

### 5. Uncommitted-changes guard

**Decision**: The skill runs `git diff --name-only chrome-extension/content.js`
before writing. If the file has uncommitted changes, the skill warns and aborts.

**Rationale**: FR-008 is explicit. `git diff` is available in the developer
environment (confirmed — project is a git repo).

---

### 6. No automated test additions needed for the skill file

**Decision**: No new test files required for this feature. The skill is a
Markdown instruction file with no independently testable logic.

**Rationale**: Constitution Principle I requires tests for non-trivial logic.
The skill file contains no logic — it is instructions for Claude. The adapter
JS code it generates will be exercised by the existing Jest test suite in
`chrome-extension/`.

**Note**: The existing Jest test file (`content.test.js` if present, or
manual Chrome reload) covers the adapter registry and merge framework.
