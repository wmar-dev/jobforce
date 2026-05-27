# Pre-Tasks Sanity Checklist: Jobforce — Superhero Job Hunt Command Center

**Purpose**: Lightweight requirements quality audit — flag critical gaps before `/speckit-tasks` is run.
**Created**: 2026-05-27
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [data-model.md](../data-model.md)
**Depth**: Lightweight (critical gaps only) | **Audience**: Peer reviewer

---

## Requirement Completeness

- [x] CHK001 — Are the input formats for the user profile fully specified — what fields are required vs. optional, and what happens if the profile is empty when Oracle or Forge runs? [Completeness, Spec §FR-006, FR-010]
  **Resolution**: `skills[]` required for Oracle (returns HTTP 400 `PROFILE_INCOMPLETE` if absent); `personal_info.name` and `personal_info.email` required for Forge PDF. All other fields optional. Documented in spec.md §FR-006, FR-007, and Clarifications §Pre-Tasks Audit.
- [x] CHK002 — Is the structured resume data format (JSON schema) defined in the spec or data model, including required fields and which sections are optional? [Completeness, data-model.md §Resume, Gap]
  **Resolution**: Full JSON schema added to data-model.md §Entity: Resume. Required fields: `personal_info.name`, `personal_info.email`, `work_history[].title`, `work_history[].company`, `work_history[].start_date`. All other fields nullable/optional.
- [x] CHK003 — Are requirements defined for how Scout deduplicates listings — by URL only, or also by title+company combination? [Completeness, Spec §FR-004, Gap]
  **Resolution**: URL-only dedup. Exact `source_url` match is the sole dedup key. Documented in spec.md Clarifications §Pre-Tasks Audit and FR-004 (unchanged — URL uniqueness already in data-model.md).
- [x] CHK004 — Are the exact question categories Coach must produce (behavioral, coding, system design, role-specific) defined for non-technical roles, or only engineering roles? [Completeness, Spec §FR-020, Gap]
  **Resolution**: 4-category schema applies universally. For non-technical roles, `coding` and `system_design` categories MAY be empty if web search yields no relevant content. LeetCode links apply only where web search indicates relevance. Documented in spec.md §FR-016 and FR-020.
- [x] CHK005 — Are requirements specified for the `config.yaml` structure — which fields are required vs. optional, and what happens if required fields are missing at startup? [Completeness, plan.md §Technical Context, Gap]
  **Resolution**: Fail fast. App refuses to start; prints missing config key path and exits with non-zero code. `config.example.yaml` documents all required and optional fields. Documented in spec.md Clarifications §Pre-Tasks Audit and tasks.md T010.

---

## Requirement Clarity

- [x] CHK006 — Is "web search" for Coach (FR-015, FR-016) defined clearly enough to determine what sources are acceptable — is it any web source, or specific sites (Glassdoor, Blind, LeetCode)? [Clarity, Spec §FR-015, Ambiguity]
  **Resolution**: Primary sources are Glassdoor, Blind, and LeetCode. General web search used as fallback if primary sources yield no results. Documented in spec.md §FR-015.
- [x] CHK007 — Is "source attribution" for Coach's web-sourced questions (FR-015) defined — what format, and what happens when a source URL is unavailable or paywalled? [Clarity, Spec §FR-015, Gap]
  **Resolution**: Each question has a `source_url` field. If source unavailable or paywalled: `source_url` is null and guidance field notes "source unavailable". Questions are not discarded due to paywall. Documented in spec.md §FR-015, data-model.md §InterviewSession question schema.
- [x] CHK008 — Is "tailored resume" (FR-011) defined clearly enough to distinguish between minor keyword adjustments and significant restructuring — is there a spec for how much Forge may reorder content? [Clarity, Spec §FR-011, Ambiguity]
  **Resolution**: Keyword/emphasis adjustments only. Forge MAY rephrase bullets and reorder items within a section. Forge MUST NOT add, remove, or fabricate bullets or jobs. Section order is preserved. Documented in spec.md §FR-011.
- [x] CHK009 — Is "fit score" (FR-007) defined with a scale and what constitutes a meaningful difference — e.g., is 0.85 vs 0.87 meaningfully different, and should scores be displayed as percentages or raw values? [Clarity, Spec §FR-007, FR-008, Ambiguity]
  **Resolution**: Scores displayed as integer percentages (e.g., 87%) with a High/Medium/Low confidence badge. Differences of ≤5 percentage points are not presented as meaningfully different. Documented in spec.md §FR-008.
- [x] CHK010 — Is the `config.yaml` seed behavior defined as idempotent — specifically, does re-running seed with an updated config update existing records or skip them? [Clarity, plan.md §research.md §7, Gap]
  **Resolution**: Idempotent by name/query. Seed skips existing Company (matched by name) and SearchConfig (matched by query+location) records. New records are inserted. Existing records are never updated by seed. Documented in spec.md Clarifications §Pre-Tasks Audit and tasks.md T014.

---

## Edge Case & Failure Mode Coverage

- [x] CHK011 — Are requirements defined for when the LaTeX renderer is unavailable (`latexmk` not installed) — is this a hard error, a degraded mode, or does Forge fall back to plain-text output? [Coverage, Spec §Assumptions, Edge Case]
  **Resolution**: Hard error. POST /api/resume/{id}/export returns HTTP 503 `{"detail": "LaTeX not available on this host"}`. UI surfaces a dismissible error banner with `latexmk` install instructions. No fallback format. Documented in spec.md §FR-012 area, Clarifications §Pre-Tasks Audit, and api-contracts.md §Forge.
- [x] CHK012 — Are requirements defined for what happens when a crawled job listing URL returns a 404 or the page has changed since crawl — does the app notify the user, and how is the stale snapshot handled? [Coverage, Spec §Edge Cases, Gap]
  **Resolution**: Out of scope for v1. Snapshot is stored at crawl time; no post-crawl URL monitoring. If the user clicks a source link and gets a 404, that is expected behavior. Documented in spec.md Clarifications §Pre-Tasks Audit.
- [x] CHK013 — Are requirements defined for what happens when Oracle is asked to rank jobs but the user profile is empty or has no skills — is this an error, a warning, or does Oracle proceed with reduced confidence? [Coverage, Spec §US2, Edge Case]
  **Resolution**: Hard error. Oracle returns HTTP 400 with `{"detail": "Profile requires at least one skill to rank jobs. Update your profile first.", "code": "PROFILE_INCOMPLETE"}`. Does not run in reduced-confidence mode. Documented in spec.md §FR-007 and Clarifications §Pre-Tasks Audit.
- [x] CHK014 — Are requirements defined for backward pipeline transitions — can a user move a listing from "Applied" back to "Saved", or are only forward transitions valid? [Coverage, data-model.md §State Transitions, Gap]
  **Resolution**: Backward transitions blocked. Only valid forward transitions per state machine are allowed. Backward transitions return HTTP 422 `{"detail": "Invalid transition: applied → saved", "code": "INVALID_TRANSITION"}`. UI disables invalid options. Documented in data-model.md §State Transitions and spec.md Clarifications §Pre-Tasks Audit.
- [x] CHK015 — Are requirements defined for the Chrome extension when the FastAPI backend is not running — is the error message and recovery path specified? [Coverage, contracts/chrome-extension-contract.md, Gap]
  **Resolution**: Extension icon shows red badge. Popup displays: "Jobforce backend is not running. Start it with: cd backend && make dev". Capture fails gracefully; no data is lost or queued. Documented in spec.md Clarifications §Pre-Tasks Audit.

---

## Consistency

- [x] CHK016 — Are the pipeline status values consistent between the spec (FR-019–022), the data model (`job_listings.status` enum), and the API contracts (`PATCH /api/jobs/{id}/status`)? [Consistency, Spec §FR-021, data-model.md, contracts/api-contracts.md]
  **Resolution**: Verified consistent. All three artifacts use: `saved`, `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`. api-contracts.md lists valid values on line 8. data-model.md §JobListing and §State Transitions match. spec.md §FR-021 and §Key Entities match.
- [x] CHK017 — Are the hero agent names (Scout, Oracle, Forge, Coach) used consistently throughout the spec, plan, data model, and API contracts — no aliases or synonyms? [Consistency, Spec §Hero Roster]
  **Resolution**: Verified consistent. All four documents use Scout, Oracle, Forge, Coach exclusively. No aliases or synonyms found across spec.md, plan.md, data-model.md, api-contracts.md, or contracts/.

---

## Non-Functional Requirements

- [x] CHK018 — Are the performance targets (SC-001–SC-011) each tied to a specific measurable condition — e.g., is "under 30 seconds" for Forge measured from user action to PDF download available, or to PDF generation complete? [Clarity, Spec §SC-001–SC-011, Ambiguity]
  **Resolution**: Measurement baselines added to spec.md §Performance Measurement Baselines. Each SC now specifies the start event (user action / request sent) and end event (result visible in UI / binary available for download). SC-008 specifically: from POST request sent to PDF binary available for download.
- [x] CHK019 — Are observability requirements for AI agent calls (Oracle, Forge, Coach) specified beyond the constitution's general logging requirement — e.g., should token usage, latency, and error rates be logged per call? [Coverage, Constitution §V, Gap]
  **Resolution**: SC-012 added to spec.md: every Oracle, Forge, and Coach API call MUST log request duration (ms), Anthropic SDK token usage (prompt + completion tokens), and error/success status to the structured backend log. Mapped to tasks.md T077.

---

## Dependencies & Assumptions

- [x] CHK020 — Is the Playwright MCP authentication flow requirement specified — when a job board requires login, is the expected user interaction (manual login in visible browser) documented as a requirement, not just a gotcha in research.md? [Completeness, research.md §4, Assumption]
  **Resolution**: Added to spec.md §Assumptions. Playwright MCP opens a visible browser window and pauses for manual login. Skill MUST print: "Please log in to [site] in the browser window, then press Enter to continue." Automated bypass is out of scope for v1.

---

## Notes

- Flag items with `[x]` when resolved; add inline comment with resolution or spec section updated.
- Items marked `[Gap]` require a spec or data-model update before proceeding to `/speckit-tasks`.
- Items marked `[Ambiguity]` may be resolved by adding a sentence to the relevant FR or assumption.
- Items marked `[Consistency]` require cross-artifact verification only — no new content needed if consistent.
