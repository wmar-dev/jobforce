# Feature Specification: Chrome Extension Job Capture for Modern Career Sites

**Feature Branch**: `003-openai-capture`

**Created**: 2026-05-27

**Status**: Implemented

**Input**: Make chrome extension work for capturing https://openai.com/careers/full-stack-software-engineer-applied-foundations-san-francisco/

## Overview

The Jobforce Chrome extension currently fails to capture job listings from modern career sites like OpenAI's that render content dynamically via JavaScript frameworks. The extension's content script uses CSS selectors tuned for simpler job boards and misses the job title, company name, location, and description on these pages — resulting in a capture failure or a blank entry. This feature improves extraction reliability so that one-click capture works on OpenAI careers (and similar modern sites) without requiring the developer to manually copy job details.

## User Scenarios & Testing

### User Story 1 — Capture a Job from OpenAI Careers (Priority: P1)

A developer browsing OpenAI's careers site clicks the Jobforce shield icon and captures the job listing. The job appears on the Jobforce dashboard with the correct title, company, location, and role type — no manual editing required.

**Why this priority**: This is the core workflow. If capture fails or produces blank fields, the extension is unusable for this site.

**Independent Test**: Navigate to `https://openai.com/careers/full-stack-software-engineer-applied-foundations-san-francisco/`, click Capture, and verify the saved job in the Jobforce dashboard shows: title = "Full Stack Software Engineer, Applied Foundations", company = "OpenAI", location = "San Francisco".

**Acceptance Scenarios**:

1. **Given** the user is on the OpenAI job listing page, **When** they click "Capture This Job", **Then** the extension extracts a non-empty title containing the job role name.
2. **Given** the user captures the job, **When** the job is saved, **Then** the company name is "OpenAI" (not empty).
3. **Given** the user captures the job, **When** the job is saved, **Then** the location field reflects the city/region from the page (e.g., "San Francisco").
4. **Given** the user has already captured the same URL, **When** they click Capture again, **Then** the popup shows "Already saved" instead of creating a duplicate.
5. **Given** the backend is offline, **When** the user clicks Capture, **Then** the popup shows a clear "Backend not running" message.

---

### User Story 2 — Graceful Fallback for Partially Structured Pages (Priority: P2)

When the extension cannot extract all fields from a page (e.g., company name is absent from the DOM), it captures what it can and saves the job with available data rather than failing entirely. The user sees which fields were auto-filled and which are missing.

**Why this priority**: Real-world pages vary. A partial capture with the URL and title is more useful than a hard failure.

**Independent Test**: Load a stripped-down career page missing company metadata. Capture should succeed with title and URL populated; company field may be empty but no error is thrown.

**Acceptance Scenarios**:

1. **Given** a page with a job title but no explicit company element, **When** the user captures, **Then** the job is saved with the title and URL; company defaults to empty string rather than throwing an error.
2. **Given** a successful partial capture, **When** the popup shows the result, **Then** the success message includes the job title so the user can confirm what was saved.

---

### Edge Cases

- Page uses a JavaScript framework (React/Next.js) — content is rendered client-side and may not be present in the initial HTML snapshot.
- The `<title>` tag contains boilerplate like "Careers at OpenAI | Full Stack..." — extraction must strip the site name suffix.
- Job description is rendered inside a shadow DOM or iframe — extraction falls back to `document.body.innerText` if structured elements are not found.
- Page content changes after initial load (lazy sections) — extraction should wait for the primary content to settle before reading.
- The URL itself contains the job title slug — can be used as a last-resort title fallback.

## Requirements

### Functional Requirements

- **FR-001**: The extension MUST extract a non-empty job title from `https://openai.com/careers/*` pages.
- **FR-002**: The extension MUST extract "OpenAI" as the company name from OpenAI careers pages.
- **FR-003**: The extension MUST extract a location value when location information is present on the page.
- **FR-004**: Extraction MUST succeed even when page content is rendered by a JavaScript framework (client-side rendered).
- **FR-005**: When all required fields (title, company) cannot be extracted, the extension MUST show a descriptive error rather than silently saving a blank job.
- **FR-006**: The extension MUST fall back to URL-slug-based title inference when DOM-based extraction fails.
- **FR-007**: The extraction logic MUST NOT break existing capture behavior on previously working job boards (LinkedIn, Greenhouse, Lever, etc.).

### Key Entities

- **Job Listing**: title, company_name, location, role_type, source_url, description, html snapshot
- **Capture Result**: ok (bool), duplicate (bool), job (saved record or null), error (string or null)

## Success Criteria

### Measurable Outcomes

- **SC-001**: Capturing the OpenAI job listing URL produces a saved job with title, company, and location all non-empty — verified in the Jobforce dashboard.
- **SC-002**: Capture completes within 3 seconds of clicking the button on a page that has already finished loading.
- **SC-003**: Zero previously-working job board captures are broken by this change — existing behavior is regression-free.
- **SC-004**: When extraction partially fails (missing company or location), the capture still succeeds and saves the URL + title rather than returning an error.

## Assumptions

- The OpenAI careers site renders its content via a JavaScript framework; the full DOM is available by the time the user manually navigates to the page and clicks the extension button.
- "Company name" for openai.com pages can be reliably inferred from the hostname (`openai.com` → `OpenAI`) when no explicit DOM element is present.
- The job title appears in the page's `<h1>` or `<title>` tag on all targeted pages.
- CI/CD pipeline and automated browser testing of the Chrome extension are out of scope; manual verification against the live URL is the acceptance test.
- No authentication or session tokens are required to view the OpenAI job listing page.
