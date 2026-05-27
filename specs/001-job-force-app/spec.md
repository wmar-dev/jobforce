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

### User Story 1 — Scout: Find Matching Jobs (Priority: P1)

The user tells Scout what kind of role they are looking for. Scout searches available
job sources, retrieves matching listings, and presents them in a mission briefing
format. This is the entry point of the entire workflow — without discovered jobs,
none of the other heroes have a target.

**Why this priority**: All other capabilities depend on having a job listing to act on.
Without job discovery, the app has no MVP.

**Independent Test**: Can be fully tested by entering a job search query and verifying
that a list of matching job listings is returned and displayed, each showing title,
company, location, and a link to apply.

**Acceptance Scenarios**:

1. **Given** the user has not yet searched for jobs, **When** they describe their target
   role and preferences to Scout, **Then** Scout returns a list of relevant job listings
   matching those criteria.
2. **Given** Scout has returned results, **When** the user views the list, **Then** each
   listing shows at minimum: job title, company name, location, and a source link.
3. **Given** a search returns no results, **When** Scout completes the search, **Then**
   the user receives a clear message that no matches were found with a suggestion to
   broaden criteria.
4. **Given** the user has run multiple searches, **When** they view their history,
   **Then** previously discovered jobs are saved and accessible without re-searching.

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
  experience, and job preferences.
- **FR-007**: Oracle MUST score each saved job listing against the user's profile
  and return an ordered ranked list.
- **FR-008**: Each score MUST be accompanied by a natural language explanation
  identifying strengths and gaps.
- **FR-009**: Scores MUST update when the user's profile changes.

#### Forge — Resume Tailoring & PDF Generation

- **FR-010**: Users MUST be able to input their resume as structured data (e.g., a
  structured file defining personal info, work history, education, skills).
- **FR-011**: Forge MUST produce a tailored resume for a selected job listing
  without fabricating experience or credentials.
- **FR-012**: Forge MUST generate a polished PDF resume from the structured resume
  data using LaTeX as the rendering engine. The LaTeX template MUST be included in
  the project and customisable.
- **FR-013**: Users MUST be able to compare the tailored content side-by-side with
  their original resume data before generating the PDF.
- **FR-014**: The generated PDF MUST be downloadable directly from the dashboard.

#### Coach — Interview Preparation

- **FR-015**: Coach MUST actively search the web for real interview questions
  reported for the target company and role, and present them with source attribution.
- **FR-016**: For technical roles, Coach MUST recommend specific LeetCode problems
  and system design questions sourced from the web that are relevant to the target
  role and level.
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
  Interviewing, Offer, or Rejected.
- **FR-022**: Every status transition MUST be recorded with a timestamp (date and
  time) forming an immutable audit log for that listing.
- **FR-023**: Users MUST be able to manually advance or update the status of any
  job listing directly from the dashboard without navigating away.
- **FR-024**: The application MUST provide a pipeline review view showing all
  listings grouped or filterable by current status, with transition timestamps
  visible on each listing's detail.
- **FR-025**: Oracle MUST exclude listings with status Offer or Rejected from
  active ranking by default, while still allowing the user to view them.

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
  Offer, Rejected.
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

---

## Clarifications

### Session 2026-05-27

- Q: What is the application's interface modality? → A: Dashboard web app — structured UI with forms, tables, and panels (not a conversational chat interface).
- Q: Where does user data live (profile, saved jobs, resumes, interview history)? → A: Local storage only — all data stored on the user's machine, no login required.
- Q: How does Scout source job listings? → A: Custom crawling tools — the app generates and ships a Chrome extension, MCP server, and/or CLI tool that the user runs to scrape and parse job listings from job sites directly into the app.
- Q: Should job listings have a trackable status lifecycle? → A: Yes — full pipeline tracking (Saved → Applied → Interviewing → Offer / Rejected) with timestamps recorded at each stage transition, plus a dedicated status review view showing the full history of state changes per listing.
- Q: Resume format — PDF import or text input? → A: No PDF import. Instead, Forge generates polished PDF resumes from a structured data file using LaTeX. Users also need: in-app status changes on the pipeline view, per-company meeting notes to track interactions, and an overview HQ dashboard showing the full job search campaign at a glance.
- Q: How should Coach source interview questions? → A: Coach MUST actively scour the web for real example interview questions specific to the role and company, recommend relevant LeetCode problems (for engineering roles), and surface system design questions drawn from web sources — not just generate questions from the job description alone.

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
