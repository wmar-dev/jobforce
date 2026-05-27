# Contract: Claude Code Skills ↔ FastAPI + MCP

Claude Code skills (`.claude/skills/`) orchestrate agent workflows by calling
FastAPI endpoints and/or MCP tools. This contract defines the interface each
skill depends on.

---

## Scout Crawl Skill (`speckit-scout-crawl`)

**MCP tools used**:
- `mcp__playwright__navigate(url)` — navigate to job listing URL
- `mcp__playwright__get_text()` — extract visible text content
- `mcp__playwright__evaluate(script)` — run JS to extract structured fields

**FastAPI calls**:
- `POST /api/ingest` — send extracted content

**Input** (passed via skill args or `.specify/feature.json`):
```
URL or list of URLs to crawl
```

**Output**: Confirmation of ingested job IDs.

---

## Oracle Rank Skill (`speckit-oracle-rank`)

**FastAPI calls**:
- `GET /api/profile` — fetch user profile for scoring context
- `GET /api/jobs?status=saved` — get unranked listings
- `POST /api/oracle/rank` — trigger AI scoring

**Input**: Optional list of job IDs; defaults to all `saved` listings.

**Output**: Ranked list with scores and rationale printed to terminal.

---

## Forge Tailor Skill (`speckit-forge-tailor`)

**FastAPI calls**:
- `GET /api/resume/base` — fetch base resume
- `GET /api/jobs/{id}` — fetch target job description
- `POST /api/resume/tailor` — create tailored variant
- `POST /api/resume/{id}/export` — download PDF

**Input**: `job_id` (required).

**Output**: Path to downloaded PDF.

---

## Coach Prep Skill (`speckit-coach-prep`)

**MCP tools used** (web search for real interview questions):
- `mcp__playwright__navigate(url)` — search Glassdoor/Blind/LeetCode
- `mcp__playwright__get_text()` — extract question lists

**FastAPI calls**:
- `GET /api/jobs/{id}` — get job description
- `POST /api/coach/prep` — persist and return full prep pack

**Input**: `job_id` (required).

**Output**: Interview prep pack displayed in terminal with LeetCode links.

---

## Shared State File

Skills that need cross-call context read/write `.specify/feature.json`:
```json
{
  "feature_directory": "specs/001-job-force-app",
  "current_job_id": 42
}
```
