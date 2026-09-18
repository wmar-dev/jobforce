# Feature Specification: Scout Crawl Deterministic Parser

**Feature Branch**: `006-scout-crawl-parser`

**Created**: 2026-05-27

**Status**: Implemented

**Input**: User description: "the scout-crawl command should use a tool and python code to parse the webpage similar to the chrome extension, so we can be more deterministic and accurate with the parsing."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture Job via Scout Crawl with Structured Parsing (Priority: P1)

A user runs `/scout-crawl <URL>` and the system uses a structured, site-aware parser — mirroring the Chrome extension's adapter registry — to extract job fields from the live page. The parsed fields are accurate and consistent rather than inferred from an LLM summarizing raw text.

**Why this priority**: This is the core improvement. Deterministic parsing eliminates variance in field extraction, reduces hallucinated values, and makes the command reliable enough to use for any supported job board.

**Independent Test**: Can be tested by running `/scout-crawl` against a known URL (e.g., an OpenAI job listing) and verifying that title, company, location, role_type, and description match the actual page content exactly, without relying on LLM interpretation.

**Acceptance Scenarios**:

1. **Given** a user runs `/scout-crawl https://openai.com/careers/some-role/`, **When** the page loads successfully, **Then** the parser uses the OpenAI site adapter (CSS selectors matching the Chrome extension) to extract title, company, location, description, and compensation, and posts them to the ingest API.
2. **Given** a URL from a job board with no site-specific adapter, **When** the page loads, **Then** the generic adapter (equivalent to the Chrome extension's `genericAdapter`) runs and extracts all available fields from standard selectors.
3. **Given** a field cannot be extracted by any selector, **When** parsing completes, **Then** the field is set to `null` and the ingest call still proceeds with the available data.

---

### User Story 2 - Parsing Logic Reuses Chrome Extension Adapter Design (Priority: P2)

The Python parsing tool mirrors the Chrome extension's two-layer architecture: a generic adapter for common selectors and a site-specific adapter registry keyed by hostname, with the specific adapter's values overriding the generic ones where non-null.

**Why this priority**: Parity with the Chrome extension ensures a single source of truth for field extraction logic. When a new site adapter is added to the Chrome extension, porting it to the skill parser should be a straightforward translation.

**Independent Test**: Can be verified by running the parser against the same URL using both the Chrome extension and `/scout-crawl`, confirming field values match.

**Acceptance Scenarios**:

1. **Given** a URL on a supported hostname, **When** the parser runs, **Then** the site-specific adapter fields take precedence over generic adapter fields when non-null/non-empty.
2. **Given** a URL on an unsupported hostname, **When** the parser runs, **Then** only the generic adapter runs, producing the best available extraction.

---

### Edge Cases

- If the page does not finish loading within 30 seconds, the tool exits with error code 1 and prints a timeout message to stderr; the ingest call is not made.
- How does the parser handle pages where the job title appears in a non-standard heading tag?
- What if the HTML returned is truncated or exceeds a size limit?
- How does the parser behave when `source_url` resolves to a redirect before landing on the job page?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The scout-crawl skill MUST invoke a Python-based parsing tool (executable via `uv run` or equivalent) to extract job fields from the captured page HTML.
- **FR-002**: The parsing tool MUST implement a generic adapter using CSS selectors equivalent to those in the Chrome extension's `genericAdapter`.
- **FR-003**: The parsing tool MUST implement a site-specific adapter registry keyed by hostname, starting with an OpenAI adapter equivalent to the Chrome extension's `openaiAdapter`.
- **FR-004**: The parsing tool MUST apply the same merge strategy as the Chrome extension: site-specific adapter fields override generic fields when non-null and non-empty.
- **FR-005**: The scout-crawl skill MUST pass only the URL to the CLI tool; the tool is responsible for fetching the page HTML itself using a headless browser.
- **FR-006**: The CLI tool MUST accept a URL as its sole input, fetch the page, parse it, and return a JSON object with fields: `title`, `company_name`, `location`, `role_type`, `description`, and optionally `compensation`.
- **FR-007**: The scout-crawl skill MUST use the parser's output fields directly as the ingest API payload, without LLM re-interpretation of those fields.
- **FR-008**: Fields that cannot be extracted MUST be set to `null`; the ingest call MUST proceed regardless.
- **FR-009**: The slug-to-location helper (converting URL path segments like `san-francisco` to `San Francisco`) MUST be ported to the Python parser.
- **FR-010**: The CLI tool MUST apply a 30-second hard timeout on page load; on timeout it MUST exit with code 1 and print a human-readable error to stderr.

### Key Entities

- **Site Adapter**: A mapping of hostname → field extractor functions using CSS selectors; equivalent to the Chrome extension's `ADAPTERS` registry.
- **Generic Adapter**: A fallback extractor using broadly applicable CSS selectors that runs for every URL.
- **Parse Result**: A structured JSON object containing the extracted job fields passed to the ingest API.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For URLs on supported hostnames, all available job fields are extracted correctly on 100% of runs (no variance between invocations for the same URL).
- **SC-002**: Field values produced by `/scout-crawl` match values produced by the Chrome extension for the same URL on supported sites.
- **SC-003**: The time to capture and ingest a job listing does not increase by more than 5 seconds compared to the current implementation.
- **SC-004**: A new site adapter can be ported from the Chrome extension to the Python parser by editing a single file.

## Assumptions

- The backend is running when `/scout-crawl` is invoked.
- The Python CLI tool runs in the existing backend virtualenv (via `uv run`) with `beautifulsoup4`, `lxml`, and `playwright` added as dependencies; Chromium is installed via `playwright install chromium`.
- The Chrome extension's adapter logic is the authoritative reference for selector choices; the Python parser mirrors it rather than diverging.
- Mobile viewport or JavaScript-rendered content differences are out of scope — the parser operates on the HTML snapshot captured by the headless browser after page load.
- Compensation is an optional field; its absence does not block ingestion.
- Login-gated pages are out of scope; the CLI tool exits with an error if it cannot reach the job content without authentication.
## Clarifications

### Session 2026-05-28

- Q: Should the CLI tool fetch the page itself (owning both fetch and parse), or should the skill pass captured HTML to the tool? → A: Tool fetches its own HTML using a headless browser; skill passes only the URL.
- Q: Should User Story 3 (login-gated page handling) be included in this feature? → A: No — removed from scope; login-gated sites handled separately.
- Q: What is the page load timeout policy for the CLI tool? → A: 30-second hard timeout; exit code 1 with error on stderr.
