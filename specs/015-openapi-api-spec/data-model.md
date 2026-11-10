# Data Model: OpenAPI Specification for the Jobforce API

No database changes. The "entities" here are the shared shapes in the API contract that this feature adds or changes. Existing response models (`JobListingOut`, `CompanyDetail`, `DashboardOut`, …) keep their fields and only gain field and model descriptions.

## BusinessError (new, response body)

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `detail` | string | yes | Human-readable text, unchanged from today |
| `code` | `ErrorCode` enum | yes | Stable machine-readable code; catalog in [contracts/error-codes.md](contracts/error-codes.md) |

The input-validation body (`HTTPValidationError`) is unchanged and separate.

## ErrorCode (new, enum)

There are 15 members; see the catalog. Each member maps to exactly one HTTP status. Members are append-only and never renamed.

## ResumeStructuredData (new, documentation-only shape)

Runtime: **not validated** on input or output (`SkipValidation`). Every field is optional and extra keys are allowed (`additionalProperties: true`).

| Field | Type |
| --- | --- |
| `personal_info` | `PersonalInfo` |
| `summary` | string \| null |
| `skills` | string[] |
| `work_history` | `WorkHistoryItem`[] |
| `education` | `EducationItem`[] |
| `projects` | `ProjectItem`[] \| null |
| `certifications` | `CertificationItem`[] \| null |
| `coursework` | `Coursework` \| null |
| `patents` | `PatentItem`[] \| null |

Nested shapes (all fields optional, extra keys allowed):

- **PersonalInfo**: name, email, phone, location, linkedin, github, website (string | null)
- **WorkHistoryItem**: company, title, start_date, end_date, location (string | null); bullets (string[])
- **EducationItem**: degree, institution, start_date, end_date, gpa, notes (string | null)
- **ProjectItem**: name, description, url (string | null); bullets (string[])
- **CertificationItem**: name, issuer (string | null); year (integer | null)
- **Coursework**: provider (string | null); courses (string[])
- **PatentItem**: title, number (string | null). Confirmed against the live `config/resume.json`.

Used by: `ResumeOut.structured_data`, `TailorRequest.structured_data`, `PUT /resume/base` request body.

## Documented string enums (documentation-only, no new runtime validation)

| Name | Values | Applied to |
| --- | --- | --- |
| `PipelineStatus` | keys of `services/scout.py::_VALID_TRANSITIONS`: saved, archived, shortlisted, applied, interviewing, offer, rejected, withdrawn | `JobListingOut.status`, `StatusPatchRequest.status`, `StatusPatchResponse.status`, `StatusTransitionOut.from/to_status`, `RecentTransitionOut.from/to_status`, `companies.JobListingSummary.status` |
| `RoleType` | full-time, part-time, contract, internship, other | `role_type` fields |
| `FitConfidence` | high, medium, low | `fit_confidence` fields |
| `QuestionCategory` | behavioral, coding, system_design, role_specific | `QuestionIn/QuestionOut.category` |

Value lists come from backend constants (the single source); exact members are confirmed during implementation.

## Tag groups (`openapi_tags`)

| Tag | Description |
| --- | --- |
| `scout` | Capture job listings from the extension and crawlers |
| `jobs` | Browse, edit, and move job listings through the pipeline |
| `oracle` | Read fit scores written by the /oracle-rank skill |
| `forge` | Base and tailored resumes, diff, and PDF export |
| `coach` | Interview prep sessions written by the /coach-prep skill |
| `dashboard` | Pipeline summary counts and recent activity |
| `companies` | Target companies, merge, and recruiter notes |

## State transitions

None introduced. `INVALID_TRANSITION` documents the existing state machine in `services/scout.py`.
