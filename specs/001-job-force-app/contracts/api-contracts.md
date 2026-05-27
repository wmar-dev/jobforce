# API Contracts: Jobforce Backend (FastAPI)

**Base URL**: `http://localhost:8000/api`
**Version**: v1
**Format**: JSON (request + response bodies)
**Auth**: None (local single-user service)

---

## Scout — Job Discovery

### POST /api/ingest
Ingest a crawled job listing (called by Chrome extension or Playwright MCP skill).

**Request**:
```json
{
  "source_url": "https://jobs.example.com/posting/123",
  "html": "<html>...</html>",
  "title": "Senior Python Engineer",
  "company_name": "Acme Corp",
  "location": "Remote, US",
  "description": "We are looking for..."
}
```
**Response 201**:
```json
{ "id": 42, "status": "saved", "company_id": 7, "duplicate": false }
```
**Response 409** (duplicate by URL):
```json
{ "id": 42, "status": "saved", "duplicate": true }
```

### GET /api/jobs
List all job listings with filters.

**Query params**: `status`, `company_id`, `min_score`, `limit`, `offset`

**Response 200**:
```json
{
  "total": 84,
  "items": [
    {
      "id": 42,
      "title": "Senior Python Engineer",
      "company": { "id": 7, "name": "Acme Corp" },
      "location": "Remote, US",
      "source_url": "https://...",
      "status": "saved",
      "fit_score": 0.87,
      "crawled_at": "2026-05-27T10:00:00Z",
      "created_at": "2026-05-27T10:00:00Z"
    }
  ]
}
```

### GET /api/jobs/{id}
Get single job listing with full details.

**Response 200**: Full job object including `description`, `fit_rationale`,
`status_history` array.

### PATCH /api/jobs/{id}/status
Advance pipeline status.

**Request**: `{ "status": "applied" }`
**Response 200**: `{ "id": 42, "status": "applied", "transitioned_at": "..." }`
**Response 422**: `{ "detail": "Invalid transition: saved → interviewing" }`

---

## Oracle — Job Ranking

### POST /api/oracle/rank
Score and rank a set of job listings against the user profile.

**Request**: `{ "job_ids": [42, 43, 44] }` (omit for all active listings)
**Response 200**:
```json
{
  "ranked": [
    { "job_id": 43, "score": 0.92, "rationale": "Strong Python + FastAPI match..." },
    { "job_id": 42, "score": 0.87, "rationale": "Missing Kubernetes experience..." }
  ]
}
```

### GET /api/oracle/rank/{job_id}
Get cached score and rationale for a single listing.

**Response 200**: `{ "job_id": 42, "score": 0.87, "rationale": "...", "scored_at": "..." }`

---

## Forge — Resume Tailoring & PDF Generation

### GET /api/resume/base
Get the user's base resume structured data.

**Response 200**: Full resume object with `structured_data` fields.

### PUT /api/resume/base
Save or update the base resume.

**Request**: `{ "label": "base", "structured_data": { ... } }`
**Response 200**: Saved resume object.

### POST /api/resume/tailor
Generate a tailored resume variant for a job listing.

**Request**: `{ "job_id": 42, "base_resume_id": 1 }`
**Response 201**:
```json
{ "id": 9, "label": "acme-swe-2026", "job_id": 42, "structured_data": { ... } }
```

### POST /api/resume/{id}/export
Generate and return a PDF from a resume's structured data via LaTeX.

**Response 200**: `Content-Type: application/pdf` — binary PDF stream.
**Response 503**: `{ "detail": "LaTeX not available on this host" }`

---

## Coach — Interview Preparation

### POST /api/coach/prep
Generate a web-sourced interview prep pack for a job listing.

**Request**: `{ "job_id": 42 }`
**Response 201**:
```json
{
  "session_id": 5,
  "job_id": 42,
  "questions": [
    {
      "id": "q1",
      "category": "behavioral",
      "text": "Tell me about a time you improved a slow system.",
      "source_url": "https://glassdoor.com/...",
      "guidance": "Use STAR format. Focus on measurable outcome."
    },
    {
      "id": "q2",
      "category": "coding",
      "text": "Two Sum",
      "leetcode_url": "https://leetcode.com/problems/two-sum/",
      "guidance": "HashMap solution is O(n). Discuss tradeoffs."
    }
  ]
}
```

### POST /api/coach/sessions/{session_id}/answer
Submit a mock interview answer and get feedback.

**Request**: `{ "question_id": "q1", "answer": "When I was at Acme..." }`
**Response 200**: `{ "question_id": "q1", "feedback": "Good use of STAR...", "score": 0.75 }`

### GET /api/coach/sessions/{session_id}/summary
Get overall mock session summary.

**Response 200**:
```json
{
  "session_id": 5,
  "overall_score": 0.71,
  "summary": "Strong on behavioral questions, needs improvement on system design...",
  "areas_to_improve": ["system design depth", "complexity analysis"]
}
```

---

## HQ Dashboard & Meeting Notes

### GET /api/dashboard
Get pipeline summary for the HQ overview.

**Response 200**:
```json
{
  "pipeline": { "saved": 12, "applied": 5, "interviewing": 2, "offer": 0, "rejected": 3 },
  "recent_transitions": [ { "job_id": 42, "title": "...", "to_status": "applied", "at": "..." } ],
  "recent_notes": [ { "id": 3, "company": "Acme", "body": "...", "created_at": "..." } ]
}
```

### POST /api/companies/{company_id}/notes
Create a meeting note.

**Request**: `{ "body": "Spoke with recruiter Sarah...", "job_listing_id": 42 }`
**Response 201**: `{ "id": 11, "company_id": 7, "body": "...", "created_at": "..." }`

### GET /api/companies/{company_id}/notes
List meeting notes for a company (reverse-chronological).

**Response 200**: `{ "items": [ { "id": 11, ... } ] }`

### GET /api/companies/{company_id}
Get company detail: all listings, statuses, and notes.

**Response 200**: Company object with embedded `job_listings[]` and `meeting_notes[]`.

---

## User Profile

### GET /api/profile
Get the user profile.

### PUT /api/profile
Save or update user profile.

**Request**: `{ "full_name": "...", "skills": [...], "experience": [...], "preferences": {...} }`
**Response 200**: Updated profile object.

---

## Chrome Extension Ingest (same as POST /api/ingest above)

The extension POSTs to `http://localhost:8000/api/ingest` from the background
service worker. No auth. The FastAPI server MUST have `localhost` in CORS
`allow_origins` when running locally.

---

## Error Response Format (all endpoints)

```json
{ "detail": "Human-readable error message", "code": "SNAKE_CASE_ERROR_CODE" }
```

HTTP status codes: 200 OK, 201 Created, 400 Bad Request, 404 Not Found,
409 Conflict, 422 Unprocessable Entity, 503 Service Unavailable.
