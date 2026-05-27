# Pre-Tasks Sanity Checklist: Jobforce — Superhero Job Hunt Command Center

**Purpose**: Lightweight requirements quality audit — flag critical gaps before `/speckit-tasks` is run.
**Created**: 2026-05-27
**Feature**: [spec.md](../spec.md) | [plan.md](../plan.md) | [data-model.md](../data-model.md)
**Depth**: Lightweight (critical gaps only) | **Audience**: Peer reviewer

---

## Requirement Completeness

- [ ] CHK001 — Are the input formats for the user profile fully specified — what fields are required vs. optional, and what happens if the profile is empty when Oracle or Forge runs? [Completeness, Spec §FR-006, FR-010]
- [ ] CHK002 — Is the structured resume data format (JSON schema) defined in the spec or data model, including required fields and which sections are optional? [Completeness, data-model.md §Resume, Gap]
- [ ] CHK003 — Are requirements defined for how Scout deduplicates listings — by URL only, or also by title+company combination? [Completeness, Spec §FR-004, Gap]
- [ ] CHK004 — Are the exact question categories Coach must produce (behavioral, coding, system design, role-specific) defined for non-technical roles, or only engineering roles? [Completeness, Spec §FR-020, Gap]
- [ ] CHK005 — Are requirements specified for the `config.yaml` structure — which fields are required vs. optional, and what happens if required fields are missing at startup? [Completeness, plan.md §Technical Context, Gap]

---

## Requirement Clarity

- [ ] CHK006 — Is "web search" for Coach (FR-015, FR-016) defined clearly enough to determine what sources are acceptable — is it any web source, or specific sites (Glassdoor, Blind, LeetCode)? [Clarity, Spec §FR-015, Ambiguity]
- [ ] CHK007 — Is "source attribution" for Coach's web-sourced questions (FR-015) defined — what format, and what happens when a source URL is unavailable or paywalled? [Clarity, Spec §FR-015, Gap]
- [ ] CHK008 — Is "tailored resume" (FR-011) defined clearly enough to distinguish between minor keyword adjustments and significant restructuring — is there a spec for how much Forge may reorder content? [Clarity, Spec §FR-011, Ambiguity]
- [ ] CHK009 — Is "fit score" (FR-007) defined with a scale and what constitutes a meaningful difference — e.g., is 0.85 vs 0.87 meaningfully different, and should scores be displayed as percentages or raw values? [Clarity, Spec §FR-007, FR-008, Ambiguity]
- [ ] CHK010 — Is the `config.yaml` seed behavior defined as idempotent — specifically, does re-running seed with an updated config update existing records or skip them? [Clarity, plan.md §research.md §7, Gap]

---

## Edge Case & Failure Mode Coverage

- [ ] CHK011 — Are requirements defined for when the LaTeX renderer is unavailable (`latexmk` not installed) — is this a hard error, a degraded mode, or does Forge fall back to plain-text output? [Coverage, Spec §Assumptions, Edge Case]
- [ ] CHK012 — Are requirements defined for when a crawled job listing URL returns a 404 or the page has changed since crawl — does the app notify the user, and how is the stale snapshot handled? [Coverage, Spec §Edge Cases, Gap]
- [ ] CHK013 — Are requirements defined for what happens when Oracle is asked to rank jobs but the user profile is empty or has no skills — is this an error, a warning, or does Oracle proceed with reduced confidence? [Coverage, Spec §US2, Edge Case]
- [ ] CHK014 — Are requirements defined for backward pipeline transitions — can a user move a listing from "Applied" back to "Saved", or are only forward transitions valid? [Coverage, data-model.md §State Transitions, Gap]
- [ ] CHK015 — Are requirements defined for the Chrome extension when the FastAPI backend is not running — is the error message and recovery path specified? [Coverage, contracts/chrome-extension-contract.md, Gap]

---

## Consistency

- [ ] CHK016 — Are the pipeline status values consistent between the spec (FR-019–022), the data model (`job_listings.status` enum), and the API contracts (`PATCH /api/jobs/{id}/status`)? [Consistency, Spec §FR-021, data-model.md, contracts/api-contracts.md]
- [ ] CHK017 — Are the hero agent names (Scout, Oracle, Forge, Coach) used consistently throughout the spec, plan, data model, and API contracts — no aliases or synonyms? [Consistency, Spec §Hero Roster]

---

## Non-Functional Requirements

- [ ] CHK018 — Are the performance targets (SC-001–SC-011) each tied to a specific measurable condition — e.g., is "under 30 seconds" for Forge measured from user action to PDF download available, or to PDF generation complete? [Clarity, Spec §SC-001–SC-011, Ambiguity]
- [ ] CHK019 — Are observability requirements for AI agent calls (Oracle, Forge, Coach) specified beyond the constitution's general logging requirement — e.g., should token usage, latency, and error rates be logged per call? [Coverage, Constitution §V, Gap]

---

## Dependencies & Assumptions

- [ ] CHK020 — Is the Playwright MCP authentication flow requirement specified — when a job board requires login, is the expected user interaction (manual login in visible browser) documented as a requirement, not just a gotcha in research.md? [Completeness, research.md §4, Assumption]

---

## Notes

- Flag items with `[x]` when resolved; add inline comment with resolution or spec section updated.
- Items marked `[Gap]` require a spec or data-model update before proceeding to `/speckit-tasks`.
- Items marked `[Ambiguity]` may be resolved by adding a sentence to the relevant FR or assumption.
- Items marked `[Consistency]` require cross-artifact verification only — no new content needed if consistent.
