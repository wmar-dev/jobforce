# Feature Specification: Jobforce — Superhero Job Hunt Command Center

**Feature Branch**: `001-job-force-app`

**Created**: 2026-05-27

**Status**: Draft

**Input**: User description: "Build an application to help me find a job with the theme of the agents being a superhero team like the avengers. I want to be able to find jobs, rank jobs, tailor resumes to jobs and prepare for job interviews."

## User Scenarios & Testing *(mandatory)*

The application is themed as a superhero command center. Each core capability is
personified as a named hero agent on the user's squad. The user is the Commander —
assembling their team and directing missions toward landing their next job.

Hero roster:
- **Scout** — finds and surfaces job listings
- **Oracle** — ranks and scores job fit
- **Forge** — tailors resumes to a target role and renders them as polished PDFs
- **Coach** — prepares the user for interviews
- **HQ Dashboard** — overview of the entire job search campaign

---

### User Story 1 — Scout: Find & Ingest Job Listings (Priority: P1)

The user browses a job board in their browser (or triggers a Playwright MCP crawl)
and captures a job listing into the app via the Chrome extension or a CLI skill. Scout
stores the raw HTML snapshot and structured listing data, then surfaces captured
listings in the Scout job board. Scout is a **push-only ingest model** — there is no
outbound search engine; the user drives discovery by navigating to job pages.

**Why this priority**: All other capabilities depend on having a job listing to act on.
Without job discovery, the app has no MVP.

**Independent Test**: Can be fully tested by navigating to a job listing URL, clicking
the Chrome extension button (or running the Playwright MCP skill), and verifying that
the listing appears in the Scout job board at `/jobs` with title, company, location,
and source link.

**Acceptance Scenarios**:

1. **Given** the user is on a job listing page, **When** they click the Chrome extension
   button or trigger the Playwright MCP skill with a URL, **Then** the listing is
   captured and appears in the Scout job board with status `saved`.
2. **Given** a listing has been captured, **When** the user views the Scout job board,
   **Then** each listing shows at minimum: job title, company name, location, source
   URL, crawled date, and current pipeline status.
3. **Given** the user captures the same URL twice, **When** the second ingest is
   attempted, **Then** the app returns a 409 conflict and does not create a duplicate.
4. **Given** multiple listings have been captured, **When** the user views the job board,
   **Then** they can filter by status (saved/applied/interviewing/offer/rejected/withdrawn),
   location, and role type to narrow the visible set.

---

### User Story 2 — Oracle: Rank Jobs by Fit (Priority: P2)

The user selects one or more discovered job listings and asks Oracle to evaluate
how well each matches their background, skills, and goals. Oracle scores each role
and explains the reasoning — helping the user prioritize which opportunities to
pursue first.

**Why this priority**: Job discovery produces volume; ranking filters that volume into
actionable priorities. Without ranking, users face decision paralysis across many
listings.

**Independent Test**: Can be tested by providing a set of job listings and a user
profile, and verifying that Oracle returns a scored, ordered list with rationale
for each score.

**Acceptance Scenarios**:

1. **Given** the user has at least one saved job listing and a profile on file,
   **When** they ask Oracle to rank their saved jobs, **Then** Oracle returns each job
   with a fit score and a brief explanation of strengths and gaps.
2. **Given** Oracle has scored jobs, **When** the user views the ranked list, **Then**
   jobs are ordered from highest to lowest fit score.
3. **Given** the user updates their profile or skills, **When** they re-run Oracle's
   ranking, **Then** scores are recalculated to reflect the updated profile.
4. **Given** a job is ranked low, **When** the user inspects it, **Then** Oracle
   identifies specific skills or experience gaps that drove the low score.

---

### User Story 3 — Forge: Tailor Resume to a Job (Priority: P3)

The user selects a target job and provides their base resume. Forge analyzes the
job description and the resume, then produces a tailored version that emphasizes
relevant experience, adjusts language to mirror the job posting, and highlights
the skills the employer is seeking.

**Why this priority**: Resume tailoring delivers direct, high-impact output for the
user but requires both a job listing (Story 1) and ideally a ranked target (Story 2)
to be most useful. It is independently testable on its own.

**Independent Test**: Can be tested by providing a base resume and a job description,
then verifying that Forge produces a revised resume that references keywords and
priorities from the job description.

**Acceptance Scenarios**:

1. **Given** the user has a base resume and a target job listing, **When** they ask
   Forge to tailor the resume, **Then** Forge returns a revised resume with language
   and emphasis adjusted to match the job description.
2. **Given** Forge has produced a tailored resume, **When** the user reviews it,
   **Then** the tailored version retains all factual content from the original and
   adds no fabricated experience.
3. **Given** Forge produces a resume, **When** the user requests it, **Then** the
   output is available in a format they can copy or download (plain text minimum).
4. **Given** the same base resume and multiple different job listings, **When** Forge
   tailors for each, **Then** each output is distinct and specific to that job.

---

### User Story 4 — Coach: Prepare for Job Interviews (Priority: P4)

The user selects a target job and asks Coach to prepare them for the interview.
Coach actively scours the web for real example interview questions reported for that
company and role, recommends relevant LeetCode problems and system design questions
sourced from the web, provides answer guidance, and runs mock interview sessions with
feedback.

**Why this priority**: Interview prep is the final phase of the job-search funnel.
It is independently valuable but most effective when targeted at a specific role
(Story 1) that the user has decided to pursue.

**Independent Test**: Can be tested by providing a job description and verifying that
Coach returns web-sourced interview questions, LeetCode recommendations, and system
design prompts specific to that role, each with answer frameworks.

**Acceptance Scenarios**:

1. **Given** the user has a target job listing, **When** they ask Coach to prepare
   them, **Then** Coach searches the web for real interview questions reported for
   that company and role, and presents them with source attribution.
2. **Given** the role is technical (engineering, data, etc.), **When** Coach prepares
   the interview pack, **Then** Coach recommends specific LeetCode problems and
   system design questions sourced from the web that are relevant to that role.
3. **Given** Coach has generated questions, **When** the user selects a question,
   **Then** Coach provides a framework or example answer the user can adapt.
4. **Given** the user wants to practice, **When** they enter mock interview mode,
   **Then** Coach asks questions one at a time, accepts the user's responses, and
   provides constructive feedback on each answer.
5. **Given** the user completes a mock session, **When** they view the summary,
   **Then** Coach provides an overall assessment with specific areas to improve.

---

### User Story 5 — HQ Dashboard: Campaign Overview & Meeting Notes (Priority: P2)

The user opens the HQ Dashboard to get a bird's-eye view of their entire job search.
They see pipeline counts by status, recent activity, and can access per-company
meeting notes to log and review every interaction (calls, emails, interviews,
recruiter conversations).

**Why this priority**: A dashboard gives the user situational awareness across all
four hero agents without having to visit each section. Meeting notes close the loop
on real-world interactions that happen outside the app. Ranked alongside Oracle (P2)
because both are about decision-making clarity rather than raw capability.

**Independent Test**: Can be tested by creating several job listings in different
statuses, writing meeting notes for one, then verifying the dashboard shows correct
counts per status and the meeting note is retrievable from the company detail view.

**Acceptance Scenarios**:

1. **Given** the user has job listings in various pipeline stages, **When** they open
   the HQ Dashboard, **Then** they see a summary of listings by status (e.g., 3 Saved,
   2 Applied, 1 Interviewing) and a timeline of recent status changes.
2. **Given** the user selects a company on the dashboard, **When** they view its
   detail, **Then** they see all job listings for that company, their current statuses,
   and all meeting notes logged for that company.
3. **Given** the user wants to log an interaction, **When** they create a meeting note,
   **Then** the note is saved with a timestamp, a free-text body, and is associated
   with a specific company and optionally a specific job listing.
4. **Given** the user has multiple meeting notes for a company, **When** they view
   the company detail, **Then** notes are displayed in reverse-chronological order.
5. **Given** the user updates a job listing's pipeline status from the dashboard,
   **When** they select a new status, **Then** the change is saved with a timestamp
   and reflected immediately across all views.

---

### Edge Cases

- What happens when a job listing URL is no longer valid or the posting has been
  taken down?
- How does the app behave if the user has no resume uploaded when requesting Forge
  or Coach?
- What if Scout returns duplicate listings from different sources for the same role?
- How does Oracle rank jobs if the user has not yet completed their profile?
- What if Forge cannot identify any matching keywords between the resume and the
  job description?
- How does Coach handle a job listing with very sparse description text?

---

## Requirements *(mandatory)*

### Functional Requirements

#### Scout — Job Discovery

- **FR-001**: Users MUST be able to describe their target role and preferences in
  natural language and have Scout ingest matching job listings from crawled sources.
- **FR-002**: Each job listing MUST display at minimum: job title, company name,
  location, and a link to the original posting.
- **FR-003**: Users MUST be able to save job listings to a personal collection for
  later reference and action.
- **FR-004**: Scout MUST deduplicate listings that represent the same role from
  multiple sources.
- **FR-005**: Users MUST be able to filter or refine their results by criteria such
  as location, role type, or recency.
- **FR-006**: The application MUST ship crawling tools in at least one of the
  following forms to allow Scout to ingest job listings from job board websites:
  a Chrome extension (captures listings while the user browses), an MCP server
  (triggered via Claude skills or agent commands), and/or a CLI tool (run locally
  to scrape and parse a target URL or site). At least one tool MUST be functional
  at v1 launch.
- **FR-007**: Crawling tools MUST parse raw job page content into structured
  Job Listing records (title, company, location, description, source URL) and
  deliver them to the local data store without manual copy-paste by the user.

#### Oracle — Job Ranking

- **FR-006**: Users MUST be able to maintain a profile describing their skills,
  experience, and job preferences. `skills[]` is the only required field; all
  other profile fields are optional. Oracle and Forge MUST block with a clear
  actionable error if their required profile fields are absent.
- **FR-007**: Oracle MUST score each saved job listing against the user's profile
  and return an ordered ranked list. Score and pipeline status are independent —
  a user may act on any listing regardless of its score. Oracle MUST return HTTP
  400 with code `PROFILE_INCOMPLETE` if the user profile has no skills.
- **FR-008**: Each score MUST be accompanied by a natural language explanation
  identifying strengths and gaps, and a confidence level (high / medium / low)
  reflecting how much signal Oracle could extract from the job description. Scores
  MUST be displayed as integer percentages (e.g., 87%) with a confidence badge.
  Differences of ≤5 percentage points MUST NOT be presented as meaningfully different.
- **FR-009**: Scores MUST update when the user's profile changes.
- **FR-009a**: When a job description is too sparse for reliable scoring, Oracle
  MUST return a low-confidence score rather than an error, and MUST surface a
  visible warning to the user that the score may not be reliable.

#### Forge — Resume Tailoring & PDF Generation

- **FR-010**: Users MUST be able to input their resume as structured data (e.g., a
  structured file defining personal info, work history, education, skills).
- **FR-011**: Forge MUST produce a tailored resume for a selected job listing
  without fabricating experience or credentials. Forge MAY rephrase bullet points,
  reorder items within a section, and emphasise matching keywords. Forge MUST NOT
  add, remove, or fabricate entire bullet points or jobs. Section order is preserved.
- **FR-012**: Forge MUST generate a polished PDF resume from the structured resume
  data using LaTeX as the rendering engine. The LaTeX template MUST be included in
  the project and customisable.
- **FR-013**: Users MUST be able to compare the tailored content side-by-side with
  their original resume data before generating the PDF.
- **FR-014**: The generated PDF MUST be downloadable directly from the dashboard.

#### Coach — Interview Preparation

- **FR-015**: Coach MUST actively search the web for real interview questions
  reported for the target company and role. Primary sources are Glassdoor, Blind,
  and LeetCode; general web search is used as fallback. Each question MUST include
  a `source_url`; if the source is unavailable or paywalled, `source_url` is null
  and the guidance field notes "source unavailable". Questions MUST NOT be discarded
  solely because a source is paywalled.
- **FR-016**: For technical roles (inferred from job title), Coach MUST recommend
  specific LeetCode problems and system design questions sourced from the web that
  are relevant to the target role and level. For non-technical roles, the coding and
  system_design question categories MAY be empty if web search yields no relevant
  content.
- **FR-017**: Each question MUST include a guidance note or example answer framework
  that the user can adapt.
- **FR-018**: Users MUST be able to enter a mock interview mode where Coach asks
  questions interactively and accepts responses.
- **FR-019**: Coach MUST provide per-answer feedback and an overall session summary
  after a mock interview.
- **FR-020**: Coach MUST distinguish question categories in its prep pack: behavioral,
  technical/coding (with LeetCode links), system design, and role-specific.

#### Application Pipeline & Status Tracking

- **FR-021**: Each job listing MUST have a pipeline status: Saved, Applied,
  Interviewing, Offer, Rejected, or Withdrawn.
- **FR-022**: Every status transition MUST be recorded with a timestamp (date and
  time) forming an immutable audit log for that listing.
- **FR-023**: Users MUST be able to manually advance or update the status of any
  job listing directly from the dashboard without navigating away.
- **FR-024**: The application MUST provide a pipeline review view showing all
  listings grouped or filterable by current status, with transition timestamps
  visible on each listing's detail.
- **FR-025**: Oracle MUST exclude listings with status Offer, Rejected, or Withdrawn
  from active ranking by default, while still allowing the user to view them.

#### HQ Dashboard & Meeting Notes

- **FR-026**: The application MUST provide an HQ Dashboard as the default landing
  view, showing: total listings by pipeline status, recent status changes, and
  quick-access links to each hero agent.
- **FR-027**: Users MUST be able to log meeting notes against a company, with each
  note storing: timestamp, free-text body, associated company, and optionally an
  associated job listing.
- **FR-028**: Meeting notes MUST be displayed in reverse-chronological order on the
  company detail view.
- **FR-029**: The HQ Dashboard MUST display recent meeting notes as part of the
  activity feed.

#### Application-wide

- **FR-030**: The application MUST present each agent (Scout, Oracle, Forge, Coach)
  with a distinct superhero identity — name, role description, and personality — as
  part of the themed experience.
- **FR-031**: Users MUST be able to navigate between agents without losing context
  about their current job target.
- **FR-032**: All user data (profile, saved jobs, resumes, session history, meeting
  notes) MUST persist across sessions using local storage on the user's machine.
  No login, account, or internet connection is required for data persistence.
- **FR-033**: The application MUST be a dashboard web app with a structured UI
  consisting of dedicated panels, tables, and forms — one section per hero agent
  plus a shared job board and HQ overview. Navigation MUST use standard web UI
  patterns (sidebar, tabs, or top nav), not a conversational chat interface.

### Key Entities

- **User Profile**: Represents the user's skills, experience, preferences, and
  job-search goals. Used by Oracle for scoring and by Coach/Forge for personalization.
- **Job Listing**: A discovered job opportunity. Contains title, company, location,
  description, source URL, fit score, current pipeline status, and a full status
  history log of timestamped transitions (e.g., Saved at 2026-05-27T10:00,
  Applied at 2026-05-28T14:32). Valid statuses: Saved, Applied, Interviewing,
  Offer, Rejected, Withdrawn.
- **Resume**: Structured data file representing the user's resume (personal info,
  work history, education, skills). Forge uses this as input to produce tailored
  content and render a polished PDF via LaTeX. Multiple resume variants may exist,
  each optionally linked to a specific Job Listing.
- **Interview Session**: A record of a mock interview run by Coach. Contains the
  job target, questions asked (with category: behavioral / coding / system design /
  role-specific), LeetCode recommendations (with links), web sources for questions,
  user responses, and Coach's feedback.
- **Agent**: One of the four hero characters (Scout, Oracle, Forge, Coach). Each
  has a defined role, personality, and set of capabilities.
- **Meeting Note**: A timestamped free-text record of an interaction with a company
  (call, email, interview, recruiter conversation). Associated with a Company and
  optionally a specific Job Listing. Stored in reverse-chronological order.
- **Company**: A grouping entity derived from job listings. Aggregates all Job
  Listings, Meeting Notes, and pipeline status changes for a single employer.
- **Crawling Tool**: A generated artifact (Chrome extension, MCP server, or CLI
  tool) that scrapes job listing pages and delivers structured Job Listing records
  to the local data store. Multiple tool forms may coexist.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can discover a list of relevant job listings from a natural
  language description in under 30 seconds.
- **SC-002**: Oracle ranks a list of 10 job listings with rationale in under
  60 seconds.
- **SC-003**: Forge produces a tailored resume for a target job in under 2 minutes.
- **SC-004**: Coach generates a full interview prep package (10+ questions with
  guidance) for a target role in under 60 seconds.
- **SC-005**: Users can complete a full mock interview session (5 questions) and
  receive a summary without leaving the application.
- **SC-006**: All user data persists correctly across at least 10 consecutive
  sessions with no data loss.
- **SC-007**: 90% of users can navigate from job discovery to tailored resume
  without external assistance.
- **SC-008**: Forge generates a downloadable LaTeX-rendered PDF resume in under
  30 seconds from a structured resume file.
- **SC-009**: The HQ Dashboard loads and displays accurate pipeline counts and
  recent activity in under 3 seconds with up to 200 saved listings.
- **SC-010**: Users can log a meeting note and have it appear in the company
  detail view without leaving or refreshing the page.
- **SC-011**: Coach delivers a web-sourced interview prep pack — including
  behavioral questions, LeetCode recommendations, and system design prompts — for
  a target role in under 90 seconds.
- **SC-012**: Every Oracle, Forge, and Coach API call MUST log: request duration
  (ms), Anthropic SDK token usage (prompt + completion tokens), and error/success
  status to the backend structured log. This enables the self-improvement loop
  described in the constitution (Principle III).

### Performance Measurement Baselines

Timing for SC-001–SC-011 is measured as follows:

- **SC-001** (Scout ingest ≤30s): from extension button click / MCP skill trigger
  to listing appearing in the Scout job board in the browser.
- **SC-002** (Oracle rank ≤60s): from POST /api/oracle/rank request sent to
  ranked results displayed in the Oracle view.
- **SC-003** (Forge tailor ≤2min): from POST /api/resume/tailor request sent to
  tailored structured data and diff displayed in the Forge view.
- **SC-004** (Coach prep ≤60s): from POST /api/coach/prep request sent to
  question pack displayed in the Coach view.
- **SC-008** (Forge PDF ≤30s): from POST /api/resume/{id}/export request sent to
  PDF binary available for download (excludes browser save dialog time).
- **SC-009** (Dashboard ≤3s): from page navigation event to all pipeline count
  cards and activity feed rendered with real data (no skeleton loaders visible).

---

## Clarifications

### Session 2026-05-27

- Q: What is the application's interface modality? → A: Dashboard web app — structured UI with forms, tables, and panels (not a conversational chat interface).
- Q: Where does user data live (profile, saved jobs, resumes, interview history)? → A: Local storage only — all data stored on the user's machine, no login required.
- Q: How does Scout source job listings? → A: Custom crawling tools — the app generates and ships a Chrome extension, MCP server, and/or CLI tool that the user runs to scrape and parse job listings from job sites directly into the app.
- Q: Should job listings have a trackable status lifecycle? → A: Yes — full pipeline tracking (Saved → Applied → Interviewing → Offer / Rejected) with timestamps recorded at each stage transition, plus a dedicated status review view showing the full history of state changes per listing.
- Q: Resume format — PDF import or text input? → A: No PDF import. Instead, Forge generates polished PDF resumes from a structured data file using LaTeX. Users also need: in-app status changes on the pipeline view, per-company meeting notes to track interactions, and an overview HQ dashboard showing the full job search campaign at a glance.
- Q: How should Coach source interview questions? → A: Coach MUST actively scour the web for real example interview questions specific to the role and company, recommend relevant LeetCode problems (for engineering roles), and surface system design questions drawn from web sources — not just generate questions from the job description alone.

### Session 2026-05-27 (Pre-Tasks Audit)

- Q: User profile fields — required vs optional? → A: `skills[]` is required to run Oracle. `full_name` is required for Forge PDF. All other profile fields (headline, experience[], preferences) are optional. Missing required fields block the relevant action with a clear, actionable error message (e.g., "Oracle requires at least one skill. Update your profile first.").
- Q: Resume structured_data schema — strict or flexible? → A: Strict schema with required fields. `personal_info.name` and `personal_info.email` are required. `work_history[]` items require `title`, `company`, `start_date`. `education[]` and `skills[]` items are optional but must conform to documented structure if present. All other fields are nullable.
- Q: Scout deduplication rule? → A: URL-only dedup. Exact `source_url` match is the sole dedup key. Cross-source duplicates (same job on LinkedIn and Greenhouse) are the user's responsibility to manage.
- Q: Coach question categories for non-technical roles? → A: The 4-category schema (behavioral, coding, system_design, role_specific) always applies. For non-technical roles, coding and system_design categories MAY be empty if web search yields no relevant content. LeetCode recommendations apply only to roles where web search indicates they are relevant (engineering, data science, ML).
- Q: config.yaml — what happens if required fields are missing at startup? → A: Fail fast. App refuses to start; prints the missing config key path and exits with a non-zero code. No defaults substitute for missing required fields.
- Q: Coach web sources — any source or specific sites? → A: Target Glassdoor, Blind, and LeetCode by default. Fall back to general web search if those yield no results. Every question must include a `source_url`; general-search results include the search result URL.
- Q: Coach source URL unavailable or paywalled? → A: Include the question, set `source_url` to null, add `"source unavailable"` to the guidance field. Do not discard questions solely because the source is paywalled.
- Q: Forge tailoring scope — how much may it restructure content? → A: Keyword and emphasis adjustments only. Forge MAY rephrase bullet points, reorder items within a section (e.g., most relevant skill first), and highlight matching keywords. Forge MUST NOT add, remove, or fabricate entire bullet points or jobs. Section order (work history, education, skills) is preserved.
- Q: Fit score display format? → A: Integer percentage (e.g., 87%) alongside a High/Medium/Low confidence badge. Differences of ≤5 percentage points are not considered meaningfully different in the UI.
- Q: config.yaml seed — idempotent on re-run? → A: Idempotent by name. Re-running seed with an updated config skips Company and SearchConfig records whose `name` or `query+location` already exist. New records are inserted. Existing records are never updated by seed; the user must edit the DB directly to change seeded values.
- Q: LaTeX unavailable behavior? → A: POST /api/resume/{id}/export returns HTTP 503 with `{"detail": "LaTeX not available on this host"}`. The frontend surfaces this as a dismissible error banner with instructions to install `latexmk`. No silent fallback or alternative format.
- Q: Stale/404 job URL? → A: The app stores a snapshot at crawl time; post-crawl URL changes are not monitored. If the user clicks the source link and gets a 404, that is expected behavior. No notification or stale-detection is required for v1.
- Q: Oracle with empty profile (skills[] empty)? → A: Oracle returns HTTP 400 with `{"detail": "Profile requires at least one skill to rank jobs. Update your profile first.", "code": "PROFILE_INCOMPLETE"}`. Oracle does not run in reduced-confidence mode with zero skills.
- Q: Backward pipeline transitions (e.g., Applied → Saved)? → A: Blocked. Only forward transitions are valid per the state machine. Backward transitions return HTTP 422 with `{"detail": "Invalid transition: applied → saved", "code": "INVALID_TRANSITION"}`. The UI disables invalid transition options.
- Q: Chrome extension — backend not running? → A: Extension icon shows a red badge. Popup displays: "Jobforce backend is not running. Start it with: cd backend && make dev". The capture attempt fails gracefully; no data is lost or queued for retry.

## Assumptions

- The user is a single job seeker (not an enterprise or recruiter use case); multi-user
  support is out of scope for v1.
- Job listings are sourced via custom crawling tools (Chrome extension, MCP server,
  and/or CLI tool) that the user runs against job board websites. No third-party
  job search API is required; the application does not host its own job database.
- The user has internet access during all agent operations. Coach specifically
  requires internet access to scour the web for interview questions, LeetCode
  problems, and system design resources.
- Resume input is structured data (a defined file format); PDF import/parsing is
  out of scope for v1. PDF output is generated via LaTeX, which must be installed
  on the user's machine or available server-side for Forge to render PDFs.
- The superhero theme is cosmetic and tonal — all four agents use the same
  underlying AI capability with different personas applied at the prompt level.
- The application is a dashboard web app targeting desktop browsers; mobile support is out of scope for v1.
- All user data is stored locally on the user's machine (no backend, no login).
  No data is shared with third parties beyond what is required for job search queries
  and AI agent calls.
- When a job board requires authentication, the Playwright MCP skill opens a visible
  browser window and pauses for the user to complete login manually before proceeding
  with the crawl. This is a documented, expected user interaction — not an error state.
  The skill MUST print a prompt: "Please log in to [site] in the browser window, then
  press Enter to continue." Automated login bypass is out of scope for v1.
