# Data Model: Jobforce — Superhero Job Hunt Command Center

**Branch**: `001-job-force-app` | **Date**: 2026-05-27

All entities are stored in SQLite (`backend/data/jobforce.db`) using SQLAlchemy 2.0
async ORM. WAL mode enabled. All tables use integer primary keys with auto-increment.
Timestamps are stored as ISO 8601 strings (UTC).

---

## Entity: Company

Represents an employer. Derived from job listings; also seedable from `config.yaml`.

```
companies
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── name            TEXT NOT NULL UNIQUE
├── domain          TEXT                        -- e.g. "acme.com"
├── notes           TEXT                        -- free-text user notes on company
├── created_at      TEXT NOT NULL               -- ISO 8601
└── updated_at      TEXT NOT NULL
```

**Constraints**: `name` is unique (case-insensitive normalisation on insert).
**Relationships**: one Company → many JobListings, many MeetingNotes.

---

## Entity: JobListing

A discovered job opportunity with full pipeline tracking.

```
job_listings
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── company_id      INTEGER NOT NULL REFERENCES companies(id)
├── title           TEXT NOT NULL
├── location        TEXT
├── description     TEXT                        -- full job description text
├── source_url      TEXT NOT NULL
├── status          TEXT NOT NULL DEFAULT 'saved'
│                   -- enum: saved | applied | interviewing | offer | rejected
├── fit_score       REAL                        -- 0.0–1.0, set by Oracle
├── fit_rationale   TEXT                        -- Oracle's explanation
├── crawled_at      TEXT                        -- when Scout captured it
├── created_at      TEXT NOT NULL
└── updated_at      TEXT NOT NULL
```

**Constraints**: `source_url` unique per company. `status` values enforced via
CHECK constraint. `fit_score` nullable until Oracle has run.

**Relationships**: one JobListing → many StatusTransitions, one PageSnapshot,
many InterviewSessions, many TailoredResumes, many MeetingNotes.

---

## Entity: StatusTransition

Immutable audit log of every pipeline stage change per listing.

```
status_transitions
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── job_listing_id  INTEGER NOT NULL REFERENCES job_listings(id)
├── from_status     TEXT                        -- NULL for initial 'saved'
├── to_status       TEXT NOT NULL
└── transitioned_at TEXT NOT NULL               -- ISO 8601, set at insert
```

**Constraints**: `to_status` values match `job_listings.status` enum.
No updates or deletes — append-only.

---

## Entity: PageSnapshot

Raw HTML archive of the crawled job listing page.

```
page_snapshots
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── job_listing_id  INTEGER NOT NULL UNIQUE REFERENCES job_listings(id)
├── html_blob       BLOB                        -- raw HTML if ≤500KB
├── file_path       TEXT                        -- relative path if >500KB
├── content_hash    TEXT NOT NULL               -- SHA-256 of raw HTML
├── size_bytes      INTEGER NOT NULL
└── captured_at     TEXT NOT NULL               -- ISO 8601
```

**Constraints**: Exactly one of `html_blob` or `file_path` is non-null (enforced
at service layer). `content_hash` enables deduplication on re-crawl.

---

## Entity: Resume

Structured resume data (base or tailored variant).

```
resumes
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── label           TEXT NOT NULL               -- e.g. "base", "acme-swe-2026"
├── is_base         INTEGER NOT NULL DEFAULT 0  -- 1 = master base resume
├── job_listing_id  INTEGER REFERENCES job_listings(id)  -- NULL for base
├── structured_data TEXT NOT NULL               -- JSON blob of resume fields
├── latex_source    TEXT                        -- rendered .tex content
├── pdf_path        TEXT                        -- path to generated PDF file
├── created_at      TEXT NOT NULL
└── updated_at      TEXT NOT NULL
```

**Constraints**: Exactly one resume may have `is_base=1`. `structured_data` stores
the full resume as JSON (personal_info, work_history[], education[], skills[]).

---

## Entity: InterviewSession

Record of a Coach prep session for a specific job.

```
interview_sessions
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── job_listing_id  INTEGER NOT NULL REFERENCES job_listings(id)
├── session_type    TEXT NOT NULL DEFAULT 'prep'
│                   -- enum: prep | mock
├── questions       TEXT NOT NULL               -- JSON array of question objects
├── overall_summary TEXT                        -- Coach's post-mock summary
├── created_at      TEXT NOT NULL
└── updated_at      TEXT NOT NULL
```

**Question object schema (JSON)**:
```json
{
  "id": "q1",
  "category": "behavioral | coding | system_design | role_specific",
  "text": "Describe a time you...",
  "source_url": "https://glassdoor.com/...",
  "leetcode_url": "https://leetcode.com/problems/...",
  "guidance": "Use STAR format...",
  "user_answer": "...",
  "coach_feedback": "..."
}
```

---

## Entity: MeetingNote

Timestamped interaction log entry per company.

```
meeting_notes
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── company_id      INTEGER NOT NULL REFERENCES companies(id)
├── job_listing_id  INTEGER REFERENCES job_listings(id)  -- optional
├── body            TEXT NOT NULL               -- free-text content
└── created_at      TEXT NOT NULL               -- ISO 8601, immutable
```

**Constraints**: `created_at` is set at insert and never updated (immutable log).
Displayed in reverse-chronological order in the UI.

---

## Entity: UserProfile

Single-row table storing the user's skills, experience, and preferences.

```
user_profiles
├── id              INTEGER PRIMARY KEY DEFAULT 1  -- always id=1
├── full_name       TEXT
├── headline        TEXT
├── skills          TEXT                        -- JSON array of skill strings
├── experience      TEXT                        -- JSON array of experience objects
├── preferences     TEXT                        -- JSON: target_roles, locations, etc.
└── updated_at      TEXT NOT NULL
```

**Constraints**: Only one row (`id=1`). UPSERT on save.

---

## Entity: SearchConfig (seed table)

Populated from `config.yaml` on first run. Read-only at runtime.

```
search_configs
├── id              INTEGER PRIMARY KEY AUTOINCREMENT
├── query           TEXT NOT NULL               -- e.g. "Senior Python Engineer"
├── location        TEXT                        -- e.g. "Remote, US"
├── source          TEXT                        -- e.g. "linkedin", "greenhouse"
└── active          INTEGER NOT NULL DEFAULT 1  -- 0 = disabled
```

---

## State Transitions: JobListing Pipeline

```
[new] → saved → applied → interviewing → offer
                    ↓           ↓           ↓
                rejected    rejected    rejected
```

Valid transitions:
- `saved` → `applied`, `rejected`
- `applied` → `interviewing`, `rejected`
- `interviewing` → `offer`, `rejected`
- `offer` → (terminal)
- `rejected` → (terminal)

Backward transitions are blocked at the service layer.

---

## Indexes

```sql
CREATE INDEX idx_job_listings_company   ON job_listings(company_id);
CREATE INDEX idx_job_listings_status    ON job_listings(status);
CREATE INDEX idx_status_transitions_job ON status_transitions(job_listing_id);
CREATE INDEX idx_meeting_notes_company  ON meeting_notes(company_id);
CREATE INDEX idx_meeting_notes_created  ON meeting_notes(created_at DESC);
CREATE INDEX idx_interview_sessions_job ON interview_sessions(job_listing_id);
```
