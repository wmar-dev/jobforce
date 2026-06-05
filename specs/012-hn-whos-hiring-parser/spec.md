# Feature Specification: Hacker News "Who's Hiring" Parser

**Feature Branch**: `012-hn-whos-hiring-parser`

**Created**: 2026-06-05

**Status**: Draft

**Input**: User description: "Add a parser specific to hacker news who's hiring to save tokens rather than using LLM to extract and process all the text. Example url: `https://news.ycombinator.com/item?id=48357725`"

## Clarifications

### Session 2026-06-05

- Q: Should the adapter handle a full thread URL and return multiple jobs, or always return one job per comment with iteration left to the skill layer? → A: Single comment per adapter call; `/scout-companies` handles thread iteration.
- Q: Should pipe-delimited parsing attempt on every comment, or only when the first line contains `|`? → A: Only attempt pipe parsing when `|` is present in the first line; fall back immediately otherwise.
- Q: Should description be stored as markdown or plain text? → A: Markdown via markdownify, consistent with all other adapters.
- Q: How should `/scout-companies` extract top-level comment URLs from an HN thread? → A: A new checked-in CLI (`hn_thread`) fetches and parses the thread page, outputs comment URLs as JSON; the skill invokes it rather than doing extraction in-context.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capture a single HN comment as a job listing (Priority: P1)

The user runs `/scout-crawl https://news.ycombinator.com/item?id=48357725` (or a deep link to a specific comment within the thread). The system deterministically extracts the job listing fields — company name, role title(s), location, role type, and description — directly from the HN comment HTML without sending the full page to an LLM. The extracted job is saved to the database.

**Why this priority**: This is the core feature. Every other story depends on structured extraction working correctly. It directly addresses the token-cost problem by eliminating LLM processing for HN pages.

**Independent Test**: Can be fully tested by running the scout CLI against a known HN hiring comment URL and verifying the extracted fields match the comment text.

**Acceptance Scenarios**:

1. **Given** a URL pointing to a specific HN "Who's Hiring" comment (e.g. `item?id=...` with `#...` anchor), **When** the scout fetch tool runs, **Then** company name, description, location, and role type are extracted deterministically from the comment text and saved without any LLM call.
2. **Given** a top-level thread URL (no anchor), **When** the scout fetch tool runs, **Then** the system returns an error or prompt indicating a specific comment anchor is required.
3. **Given** a comment that contains multiple roles, **When** the scout fetch tool runs, **Then** a single job listing is created using the company name and the full comment body as the description.

---

### User Story 2 - Capture all jobs from a monthly HN thread (Priority: P2)

The user adds the "Ask HN: Who is hiring?" thread URL to their target companies config. The `/scout-companies` skill iterates over all top-level comments in the thread, calls the HN adapter for each individual comment URL, and bulk-ingests them into the database — skipping duplicates already present.

**Why this priority**: Bulk ingestion from a monthly thread is the high-value use case that makes HN a first-class source. The adapter itself stays single-comment, single-job; `/scout-companies` handles the iteration.

**Independent Test**: Can be tested by running `/scout-companies` with an HN thread URL in `config.yaml` and verifying the job count in the database increases by the number of unique top-level comments.

**Acceptance Scenarios**:

1. **Given** a thread URL with 50 top-level job comments, **When** `/scout-companies` runs, **Then** up to 50 new job listings are created (minus any duplicates already in the database).
2. **Given** the same thread URL is ingested twice, **When** the second ingest runs, **Then** no duplicate rows are created; the tool reports how many were skipped.
3. **Given** a comment that is flagged, dead, or has no text, **When** ingest runs, **Then** that comment is silently skipped.

---

### User Story 3 - Structured field extraction from comment text (Priority: P1)

The comment body follows informal but consistent conventions used by HN posters (e.g. `Company Name | Role | Location | Remote/Onsite | Full-time`). The parser extracts structured fields from this first line where possible, falling back to treating the full comment as an unstructured description.

**Why this priority**: Structured extraction makes the saved jobs useful immediately — the title, location, and role type fields are populated without manual editing.

**Independent Test**: Can be tested by running the parser against a set of representative HN comment fixtures and asserting extracted field values.

**Acceptance Scenarios**:

1. **Given** a comment starting with `Acme | Senior Engineer | San Francisco | Remote OK | Full-time`, **When** the parser runs, **Then** `company_name=Acme`, `title=Senior Engineer`, `location=San Francisco / Remote OK`, `role_type=full-time` are extracted.
2. **Given** a comment that does not follow the pipe-delimited format, **When** the parser runs, **Then** `company_name` is extracted from the first line and `description` is the full comment body; `title`, `location`, `role_type` are left null or inferred from the body text.
3. **Given** a comment with a `| REMOTE |` or `| ONSITE |` token, **When** the parser runs, **Then** the location field reflects the remote/onsite designation.

---

### Edge Cases

- What happens when the HN page is rate-limited or temporarily unavailable? The scout fetch tool should surface the HTTP error and not create a partial record.
- How does the system handle comments with non-English text? They are treated as opaque descriptions — no parsing attempted beyond the first line.
- What if the HN item ID is not a "Who's Hiring" thread (e.g. a regular Ask HN)? The parser runs anyway; the results may be lower quality but no special-casing is needed.
- What happens when a comment contains HTML entities or markdown-like formatting? The description is converted to markdown via `markdownify`, consistent with all other site adapters.
- What if the thread has paginated comments (HN loads more via `?p=2`)? Pagination handling is out of scope for v1; only comments on the first page are ingested.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support `news.ycombinator.com` as a recognised site in the parse service, routing HN URLs through a dedicated adapter rather than the generic adapter.
- **FR-002**: The HN adapter MUST extract the job description from the comment body text without invoking any LLM.
- **FR-003**: The HN adapter MUST attempt pipe-delimited extraction of `company_name`, `title`, `location`, and `role_type` from the first line ONLY when that line contains a `|` character; if no `|` is present the adapter falls back immediately without attempting structured parsing.
- **FR-004**: When a first-line field cannot be reliably extracted, the system MUST fall back gracefully: `company_name` defaults to the first non-empty token of the first line; other fields are left null or inferred from body text using the existing role-type keyword scan.
- **FR-005**: The HN adapter MUST handle both deep-link comment URLs (with `#` anchor) and direct `item?id=<comment-id>` URLs pointing to a single comment.
- **FR-006**: The adapter MUST skip dead, flagged, or empty comments; the `/scout-companies` skill is responsible for iterating comments and calling the adapter per comment URL.
- **FR-007**: The existing `scout_fetch` CLI and `/scout-crawl` skill MUST work unchanged against individual HN comment URLs — no new CLI flags or skill changes are required. Thread-level iteration is handled by `/scout-companies`.
- **FR-009**: A new checked-in CLI module (e.g. `python -m jobforce.cli.hn_thread <thread_url>`) MUST fetch the HN thread page, extract all top-level comment URLs as `https://news.ycombinator.com/item?id=<comment-id>`, and print them as a JSON array to stdout. Dead and flagged comments MUST be excluded.
- **FR-010**: The `/scout-companies` skill MUST detect when a target URL is an HN thread (hostname `news.ycombinator.com`), invoke the `hn_thread` CLI to retrieve comment URLs, then call `scout_fetch` for each URL — no in-skill HTML parsing or LLM extraction of comment URLs.
- **FR-008**: The adapter MUST be testable with static HTML fixtures, consistent with the existing test pattern in `tests/unit/test_parse_service.py`.

### Key Entities

- **HN Comment**: A top-level comment on a "Who's Hiring" thread. Key attributes: comment ID, author, timestamp, body HTML. Maps to one `job_listing` row.
- **Pipe-delimited Header**: The optional first line of an HN comment following the `Company | Role | Location | ...` convention. Used to populate structured fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Ingesting a known HN "Who's Hiring" comment produces a saved job listing with `company_name` populated in 100% of test cases.
- **SC-002**: Structured field extraction (title, location, role_type) succeeds for at least 70% of comments that follow the pipe-delimited convention, as verified by unit tests against representative fixtures.
- **SC-003**: The full HTML of an HN thread page is never sent to an LLM during ingest — zero LLM calls for the parse step, verified by the absence of any `anthropic` import or API call in the adapter code.
- **SC-004**: Ingesting a 50-comment HN thread completes in under 60 seconds on a standard development machine.
- **SC-005**: Running the existing parse service test suite after adding the adapter produces no regressions.

## Assumptions

- The HN HTML structure for `news.ycombinator.com/item?id=<id>` is stable enough for BeautifulSoup CSS selectors (`.commtext`, `.hnuser`, `.score`). This is consistent with how other adapters in `parse.py` are built.
- Bulk ingestion of a full thread is out of scope for the backend `parse.py` adapter itself; bulk iteration is handled by the `/scout-companies` skill, which will be extended to support HN thread URLs as a target.
- The `source_url` stored for each job will be the canonical comment URL (`https://news.ycombinator.com/item?id=<comment-id>`), not the thread URL.
- The HN "Who's Hiring" thread is a publicly accessible page with no login required.
- Only top-level comments are treated as job postings; nested replies are ignored.
- The feature does not include any UI changes — the saved jobs appear in the existing jobs table like any other ingested listing.
