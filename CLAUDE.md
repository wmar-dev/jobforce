# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Is

Jobforce is a personal job search assistant. It has three components:

- **Backend** — FastAPI async service (Python 3.12, SQLite/SQLAlchemy, uv)
- **Frontend** — Next.js 15 dashboard (React 18, Tailwind, SWR)
- **Chrome Extension** — Manifest V3, captures job listings while browsing

AI reasoning runs in Claude Code skills (`.claude/skills/`), not in the backend. The only exception is Coach (`backend/jobforce/services/coach.py`), which calls the Anthropic SDK directly. All other AI work (Oracle ranking, Forge tailoring) happens in skills.

**Verify this invariant**: `grep -r "import anthropic" backend/` → zero results (except `services/coach.py`).

---

## Commands

### Root

```bash
make install   # Install backend + frontend deps
make dev       # Start backend (:8000) + frontend (:3000) concurrently
make check     # All quality gates (lint + typecheck + test)
make seed      # Seed DB from config.yaml + config/resume.json
```

### Backend (`cd backend`)

```bash
make dev       # uvicorn --reload on :8000
make check     # lint + typecheck + test (must all pass)
make lint      # ruff check + ruff format --check
make typecheck # mypy strict
make test      # pytest with coverage
make sync      # uv sync (lock/sync pyproject.toml)

# Single test
uv run pytest tests/unit/test_forge.py::test_compute_diff -xvs
```

### Frontend (`cd frontend`)

```bash
npm run dev    # Next.js dev server on :3000
npm run build  # Production build
npm run lint   # ESLint + TS check
npm test       # Jest
npm test -- --watch  # Jest watch
```

### Database

```bash
cd backend && uv run python -m jobforce.db.init  # Create schema
cd backend && uv run python -m jobforce.db.seed  # Seed from config
```

API docs: <http://localhost:8000/docs>

---

## Architecture

### Skill-Driven AI (the key pattern)

```text
User → /oracle-rank skill → GET /api/jobs + GET /api/resume/base
                          → Claude reasons, scores jobs
                          → PATCH /api/jobs/{id} with fit_score/rationale
                          → Frontend displays ranked jobs
```

Skills are in `.claude/skills/{name}/SKILL.md`. They fetch from the API, reason in-context, then write results back.

### Backend Structure

```text
backend/jobforce/
├── main.py          # FastAPI app + lifespan hook
├── config.py        # YAML config (Pydantic)
├── db/
│   ├── models.py    # 8 SQLAlchemy tables (see below)
│   ├── engine.py    # Async session factory
│   ├── init.py      # create_all()
│   └── seed.py      # Seed from config.yaml + resume.json
├── routers/         # One file per domain (jobs, forge, oracle, coach, ingest, dashboard, companies)
└── services/        # Business logic; routers stay thin
```

### Key DB Tables

| Table                | Purpose                                                                        |
| -------------------- | ------------------------------------------------------------------------------ |
| `job_listings`       | Captured postings; `fit_score`, `fit_rationale` written by Oracle skill        |
| `resumes`            | `is_base=1` is canonical profile; `is_base=0` rows are tailored (per job)      |
| `status_transitions` | Audit trail for pipeline moves                                                 |
| `companies`          | Company targets + recruiter notes                                              |
| `meeting_notes`      | Notes per company/job from recruiter calls                                     |
| `interview_sessions` | Coach-generated prep questions                                                 |

Resume `structured_data` is a JSON string with keys: `headline`, `skills`, `experience` (company/title/duration/bullets), `education`.

### Frontend Structure

```text
frontend/src/
├── app/             # Next.js App Router pages (page.tsx per route)
├── components/      # UI grouped by domain (jobs/, forge/, dashboard/, etc.)
├── hooks/           # SWR data hooks (useJobs, useJob, useDashboard, useProfile)
└── lib/             # api.ts (fetch wrappers), types.ts
```

SWR polls every 30s. Backend CORS allows `localhost:3000` only.

### Notable API Endpoints

| Endpoint | Purpose |
| -------- | ------- |
| `POST /api/jobs/{id}/reparse` | Re-extract `title`, `location`, `role_type`, `description` from the stored HTML snapshot using the current site adapter in `services/parse.py`. Use after fixing or adding a site adapter to refresh already-ingested jobs without re-crawling. Returns 404 if no snapshot exists. |
| `PATCH /api/jobs/{id}/status` | The **only** way to change a job's pipeline `status` (e.g. mark `rejected`, `applied`). Body: `{"status": "<new_status>"}`. Validates the transition against the state machine in `services/scout.py` (`_VALID_TRANSITIONS`) and records a row in `status_transitions`. Returns 422 with `code: "INVALID_TRANSITION"` if the transition isn't allowed. The general `PATCH /api/jobs/{id}` endpoint rejects a `status` field with 422 (`extra_forbidden`) — use this endpoint instead. See the `/scout-reject` skill. |
| `GET /api/jobs?source_url=<url>` | Exact-match lookup by `source_url` — use this to check whether a job listing URL is already captured before crawling. Bypasses the default archived/withdrawn/rejected exclusion (matches regardless of pipeline status), mirroring the dedup check in `services/scout.py::ingest_listing`. Returns `{"total": 0, "items": []}` if not found. |
| `GET /api/jobs?company=<substr>` | Case-insensitive substring match on company name (no need to look up `company_id` first via `GET /api/companies`). Combine with `company_id` for an exact match instead. |
| `POST /api/jobs/bulk-archive?company_id=<id>` | Default (no `all_active`): archives only `saved` jobs for the company with `fit_score < 0.50`, skipping `shortlisted`/unscored/pipeline-stage jobs. Pass `all_active=true` to instead archive **every** `saved`/`shortlisted` job for that company regardless of score — use this for "archive all jobs from company X" requests instead of looping `PATCH /api/jobs/{id}/status`. `all_active=true` requires `company_id` (422 otherwise). |

### Chrome Extension

Content scripts in `chrome-extension/content.js` have per-domain extractors. When a job page is open, the extension posts to `POST /api/jobs/ingest`. No AI in the extraction path — deterministic parsing only.

---

## Configuration

Two gitignored files are required at runtime:

- `config.yaml` — copy from `config.example.yaml`; sets DB path, search queries, user preferences
- `config/resume.json` — copy from `config/resume.example.json`; seeded as the base resume on startup

---

## Current Feature Context

Feature 011 (coach skill migration) is **complete**. The `anthropic` Python package has been removed from the backend.

Key changes:

- `backend/pyproject.toml` — `anthropic>=0.105.0` dependency removed; `uv.lock` regenerated
- `backend/jobforce/services/coach.py` — rewritten: SDK removed; `store_prep_pack()` replaces `generate_prep_pack()`; `evaluate_answer()` is now a stub
- `backend/jobforce/routers/coach.py` — `PrepRequest` now requires a `questions: list[QuestionIn]` field; backend stores questions provided by the skill, no AI call on the backend path
- `backend/tests/contract/test_coach.py` — updated: no more mock patches; tests POST real question lists
- `.claude/skills/coach-prep/SKILL.md` — rewritten: skill generates questions via in-context Claude reasoning (Pro subscription), then POSTs them to the backend; sessions appear in the web UI unchanged

**Verify invariant**: `grep -r "import anthropic" backend/` → zero results

<!-- SPECKIT START -->
Active feature plan: specs/013-forge-tex-pdf/plan.md
<!-- SPECKIT END -->
