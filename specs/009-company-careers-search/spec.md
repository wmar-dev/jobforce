# Feature Specification: Company Careers Search Skill

**Feature Branch**: `009-company-careers-search`

**Created**: 2026-05-28

**Status**: Implemented

**Input**: User description: "Add functionality to search the career pages of target_companies from config.yaml. Maybe this should be a skill?"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crawl All Target Company Career Pages (Priority: P1)

The user invokes `/scout-companies` (or similar) and the skill visits the careers page of every company listed under `search.target_companies` in `config.yaml`, discovers open job listings, and ingests any new ones into Jobforce.

**Why this priority**: The core ask — convert the inert `target_companies` list into actionable job discovery with no per-URL manual work.

**Independent Test**: With 2+ companies in `config.yaml`, invoking the skill results in new job listings appearing in the Jobforce board sourced from those companies' careers pages.

**Acceptance Scenarios**:

1. **Given** `config.yaml` has 2 target companies, **When** the user runs the skill, **Then** the skill visits each company's careers page, discovers open roles, and ingests them via the existing ingest API.
2. **Given** a job listing already exists in the board, **When** the skill re-crawls that company, **Then** the duplicate is skipped (409) and not double-counted.
3. **Given** a company's careers page requires login, **When** the skill attempts to crawl it, **Then** the skill reports the failure for that company and continues with the remaining companies.

---

### User Story 2 - Per-Company Careers URL Override (Priority: P2)

The user can optionally specify a direct `careers_url` for a company in `config.yaml` to bypass auto-discovery (e.g., when the company uses a non-standard careers page path or a hosted ATS URL like Greenhouse/Lever).

**Why this priority**: Auto-discovery of careers URLs will fail for many companies (ATS-hosted pages, non-standard paths). An override is the practical escape hatch.

**Independent Test**: With `careers_url: "https://boards.greenhouse.io/acme"` set for one company, invoking the skill uses that URL directly rather than attempting to find the careers page.

**Acceptance Scenarios**:

1. **Given** a company has `careers_url` set, **When** the skill runs, **Then** it uses that URL directly as the crawl starting point.
2. **Given** a company has no `careers_url`, **When** the skill runs, **Then** it attempts to discover the careers page from the company's `domain`.

---

### User Story 3 - Crawl a Single Company (Priority: P3)

The user invokes the skill with a specific company name to crawl only that company rather than all target companies.

**Why this priority**: Useful for testing a new company entry or re-scanning one company without waiting for the full run.

**Independent Test**: Running the skill with a company name argument only crawls that one company and reports results for it alone.

**Acceptance Scenarios**:

1. **Given** a company name is passed as an argument, **When** the skill runs, **Then** only that company's careers page is crawled.
2. **Given** an unrecognized company name is passed, **When** the skill runs, **Then** it reports "Company not found in config.yaml" and exits cleanly.

---

### Edge Cases

- What happens when a company's domain has no detectable careers page? → Report as "careers page not found" for that company and continue.
- What happens when the careers page returns no open listings? → Report "0 jobs found" for that company; not an error.
- What happens when the backend is not running? → Fail immediately with a clear message before crawling begins.
- What happens when a company is in the `companies` DB table but not in `config.yaml`? → Out of scope; only config.yaml entries are crawled.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The skill MUST read `search.target_companies` from `config.yaml` to determine which companies to crawl.
- **FR-002**: For each company without a `careers_url`, the skill MUST attempt to locate the careers page by navigating to the company domain and following standard patterns (e.g., `/careers`, `/jobs`).
- **FR-003**: For each company with a `careers_url` set, the skill MUST use that URL directly as the crawl starting point.
- **FR-004**: The skill MUST extract individual job listing URLs from the careers page and ingest each one using the existing `POST /api/ingest` endpoint.
- **FR-005**: The skill MUST report a per-company summary: jobs ingested, duplicates skipped, and failures.
- **FR-006**: The skill MUST continue crawling remaining companies if one company's crawl fails.
- **FR-007**: The `CompanyConfig` model MUST be extended to include an optional `careers_url` field.
- **FR-008**: The skill MUST reuse the existing `scout_fetch` CLI tool (or its underlying parser) to extract structured job data from each listing URL.

### Key Entities

- **CompanyConfig** (extended): Adds optional `careers_url: str` field to the existing `name` + `domain` config model.
- **CrawlResult**: Per-company outcome — company name, jobs ingested count, duplicates skipped count, errors list.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A user with 5 companies in `config.yaml` can discover and ingest all open roles from those companies' career pages in a single skill invocation.
- **SC-002**: Companies that fail to crawl do not prevent other companies from being processed — at least N-1 companies are attempted when one fails.
- **SC-003**: Duplicate listings are handled silently; the final report counts only net-new ingestions.
- **SC-004**: The skill completes a crawl of 5 companies and reports results within a reasonable interactive time (under 3 minutes for typical career pages with fewer than 50 listings each).

## Assumptions

- The skill follows the same pattern as `/scout-crawl`: it runs as a Claude Code skill (`.claude/skills/`), using Playwright MCP for browser interaction, and calls the existing backend ingest API.
- No new backend endpoints are needed — the existing `POST /api/ingest` handles individual job ingestion.
- Career page discovery for domains without `careers_url` will try a small fixed set of common paths (`/careers`, `/jobs`, `/openings`) before giving up.
- Login-gated career pages are out of scope; the skill will report and skip them.
- The skill operates against whatever `config.yaml` entries exist at runtime — it does not read from the `companies` DB table.
- The backend must be running locally for the skill to ingest jobs.
- PDF generation, Oracle scoring, and Forge tailoring are out of scope for this feature.
