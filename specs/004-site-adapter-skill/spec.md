# Feature Specification: Site Adapter Skill

**Feature Branch**: `004-site-adapter-skill`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "use playwright mcp server to check format of a job posting URL and update google chrome extension code to parse page. Make a claude skill that can take a url and update the chrome extension."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Inspect and Capture Job Page Format (Priority: P1)

A developer opens Claude Code and runs a skill command with a job posting URL.
The skill navigates to the page, captures its structure, and extracts the key
data fields available (title, company, location, description, compensation,
role type). The developer sees a structured summary of what was found on the
page and what fields could be extracted.

**Why this priority**: This is the foundational step — without it, there is
nothing to generate an adapter from. It delivers standalone value as a
diagnostic/research tool even before the adapter is written.

**Independent Test**: Can be fully tested by running the skill with any job
posting URL and verifying a structured field summary is returned with no
adapter code changes made.

**Acceptance Scenarios**:

1. **Given** a valid job posting URL, **When** the skill is invoked, **Then**
   the skill navigates to the page and returns a structured summary of all
   extractable fields (title, company, location, description, compensation,
   role type) with the raw values found.
2. **Given** a URL for a site that already has an adapter, **When** the skill
   is invoked, **Then** the skill still inspects the live page and reports
   current field values alongside what the existing adapter would extract,
   highlighting any gaps or regressions.
3. **Given** a URL that returns an error or non-job page, **When** the skill
   is invoked, **Then** the skill reports the failure clearly with a
   human-readable message and exits without modifying any code.

---

### User Story 2 - Generate or Update Chrome Extension Adapter (Priority: P2)

After inspecting the page, the skill generates or updates a site-specific
adapter in the Chrome extension's content script so the extension can reliably
extract structured job data from that site in the future.

**Why this priority**: This is the primary output of the feature — producing
working adapter code. It depends on US1 (page inspection) completing first.

**Independent Test**: Can be fully tested by running the skill end-to-end on
a URL, then loading the updated extension in Chrome and triggering a capture
on that same URL to verify the extracted fields are accurate.

**Acceptance Scenarios**:

1. **Given** a job posting URL for a site with no existing adapter, **When**
   the skill completes inspection, **Then** a new site-specific adapter is
   added to the Chrome extension content script keyed by the site's hostname,
   and the generic fallback still applies for any fields the adapter does not
   explicitly handle.
2. **Given** a job posting URL for a site that already has an adapter,
   **When** the skill completes inspection, **Then** the existing adapter is
   updated to reflect the current page structure, and no duplicate adapter
   entry is created.
3. **Given** the skill generates adapter code, **When** the code is saved,
   **Then** the existing adapter registry structure and merge framework in the
   content script are preserved unchanged; only the site-specific adapter
   object is added or modified.
4. **Given** a job posting page where a field (e.g., compensation) is not
   present in the DOM, **When** the skill generates the adapter, **Then** that
   field is omitted from the adapter rather than producing a null or empty
   extractor.

---

### User Story 3 - Skill Reusability Across Sites (Priority: P3)

The skill works repeatably for any job board URL, not just OpenAI. A developer
can run it against Greenhouse, Lever, LinkedIn, or any other job board and get
a valid adapter each time.

**Why this priority**: Generalisation multiplies the value of US1 and US2 but
is not required for the initial MVP. OpenAI careers is validated first.

**Independent Test**: Can be fully tested by running the skill against three
distinct job board hostnames and verifying a distinct adapter entry is created
for each, all coexisting in the content script without conflict.

**Acceptance Scenarios**:

1. **Given** job posting URLs from three different hostnames, **When** the
   skill is run for each, **Then** three distinct adapter entries exist in the
   content script, one per hostname.
2. **Given** an adapter already exists for hostname A, **When** the skill is
   run for a new URL on hostname B, **Then** the adapter for hostname A is
   unchanged.

---

### Edge Cases

- What happens when the job page requires JavaScript rendering to show content
  (lazy-loaded, SPA)? The skill MUST wait for the primary content region to be
  fully rendered before capturing field values.
- What happens when the page structure changes between skill runs? The updated
  adapter replaces the old one; no stale selectors are retained.
- What happens when two job postings from the same hostname have different DOM
  structures? The adapter MUST use the most general selector that works for
  both; if ambiguous, the skill SHOULD note the discrepancy to the developer.
- What happens when the content script already has uncommitted local edits?
  The skill MUST not overwrite unsaved work; it MUST warn the developer and
  stop.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The skill MUST accept a job posting URL as its sole required input.
- **FR-002**: The skill MUST navigate to the URL and capture a structured
  representation of the page's content fields (title, company name, location,
  job description body, compensation, role type) using the live page DOM.
- **FR-003**: The skill MUST produce a human-readable summary of what fields
  were found and their extracted values before modifying any code. Fields not
  found on the page MUST be listed as "(not found)" in the summary.
- **FR-004**: The skill MUST add or update the site-specific adapter in the
  Chrome extension content script (`chrome-extension/content.js`) keyed by
  the URL's hostname. The adapter is written for all fields successfully
  extracted; fields not found are omitted from the adapter (not set to null).
- **FR-005**: The skill MUST preserve the existing adapter registry structure,
  generic adapter, and merge framework — only the named adapter object for the
  target hostname is added or replaced.
- **FR-006**: The skill MUST handle the case where an adapter for the hostname
  already exists by updating it in place rather than duplicating it.
- **FR-007**: The skill MUST NOT modify any code if the page navigation fails
  entirely. Partial field extraction (some fields found, some not) is NOT
  treated as a failure — the skill proceeds and writes the adapter for the
  fields it did find, reporting missing fields in the completion output.
- **FR-008**: The skill MUST warn the developer and abort if the content script
  has uncommitted changes that would be overwritten.
- **FR-009**: The skill MUST be invocable as a Claude Code slash command with
  a URL argument (e.g., `/site-adapter-update <url>`).
- **FR-010**: The skill MUST NOT make any calls to external AI APIs or SDKs;
  all intelligence is provided by Claude Code's built-in capabilities.

### Key Entities

- **Job Posting Page**: A web page at a given URL containing structured job
  information; characterised by its hostname and DOM field locations.
- **Site Adapter**: A named JavaScript object mapping field names to extractor
  functions, keyed by hostname and registered in the Chrome extension's adapter
  registry.
- **Field Summary**: A structured, human-readable report of field names and
  their extracted values from a live page inspection.
- **Content Script**: The Chrome extension file (`content.js`) that hosts all
  adapters, the generic fallback, and the merge framework.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can run the skill against any job posting URL and
  receive a complete field summary in under 30 seconds.
- **SC-002**: After the skill runs, the Chrome extension correctly captures all
  available structured fields from the target site with zero manual code edits
  required.
- **SC-003**: The skill produces a working adapter for at least 5 distinct job
  board sites without modification to the skill itself.
- **SC-004**: 100% of existing adapter entries and the generic fallback remain
  intact after any skill run (no regressions to previously supported sites).
- **SC-005**: The skill can be run repeatedly on the same URL without creating
  duplicate adapter entries or corrupting the content script.

## Clarifications

### Session 2026-05-27

- Q: When some fields are found but others are missing, should the skill proceed to write an adapter or stop? → A: Proceed with partial extraction — write adapter for fields found, report missing fields in completion report.

## Assumptions

- The Chrome extension content script (`chrome-extension/content.js`) is the
  single source of truth for all site adapters; no secondary adapter registry
  exists.
- Job posting pages are publicly accessible without authentication; pages
  behind login walls are out of scope for v1.
- The existing adapter registry format (keyed by hostname, each value an object
  of field-name → function) is the target format for generated adapters.
- The Playwright MCP server is already configured and available in Claude Code;
  the skill does not install or configure it.
- Mobile-only or app-only job boards (no public web URL) are out of scope.
- The skill runs in a developer's local environment; no CI or automated
  pipeline execution is required for v1.
