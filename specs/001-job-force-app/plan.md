# Implementation Plan: Jobforce — Superhero Job Hunt Command Center

**Branch**: `001-job-force-app` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-job-force-app/spec.md`

---

## Summary

Build a superhero-themed job search command center with four AI hero agents (Scout,
Oracle, Forge, Coach) plus an HQ Dashboard. The stack is Next.js 14 frontend +
FastAPI backend + SQLite storage, orchestrated via Claude Code skills. Job listings
are crawled via a Playwright MCP skill and a Chrome Extension (Manifest V3). Resumes
are generated as PDFs using LaTeX. All data is local; no login required.

---

## Technical Context

**Language/Version**: Python 3.14 (backend), TypeScript / Node.js 20 (frontend),
JavaScript MV3 (Chrome extension)

**Primary Dependencies**:

- Backend: FastAPI, SQLAlchemy 2.0 async, aiosqlite, Pydantic v2, pydantic-settings[yaml],
  Jinja2, anthropic SDK, ruff, mypy, pytest, pytest-asyncio, pytest-cov
- Frontend: Next.js 14, React 18, TypeScript, Tailwind CSS, shadcn/ui, SWR
- Extension: Chrome MV3 (vanilla JS, no bundler required for v1)
- Tooling: Claude Code CLI, Playwright MCP (`@playwright/mcp`)

**Storage**: SQLite via SQLAlchemy async (`aiosqlite`), WAL mode enabled,
file at `backend/data/jobforce.db`. Raw HTML BLOBs in `page_snapshots` table
(≤500KB inline, larger stored at `backend/data/pages/`).

**Testing**:

- Backend: pytest + pytest-asyncio + pytest-cov (target: 100% pass, no coverage regression)
- Frontend: Jest + React Testing Library
- Extension: Manual test script in `chrome-extension/tests/`
- Contract tests: pytest hitting live FastAPI test client (no mocks for DB)

**Target Platform**: macOS/Linux desktop, Chrome browser, local network only

**Project Type**: Web application (frontend + backend) + browser extension + CLI skills

**Performance Goals**:

- Job ingest (Scout): <2s per listing
- Oracle ranking (10 jobs): <60s
- Forge PDF generation: <30s
- Coach prep pack (web search + questions): <90s
- HQ Dashboard load (200 listings): <3s

**Constraints**:

- Local only — no cloud deployment, no user auth
- LaTeX must be installed on host (documented in quickstart)
- SQLite single-writer — bulk crawl ingest must serialize
- No PDF import — structured data input only for Forge

**Scale/Scope**: Single user, up to ~500 job listings, ~100 companies

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### Pre-Phase 0 Gates

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Test-First | ✅ PASS | Test strategy defined per layer (pytest, Jest, contract tests) |
| II. Code Quality | ✅ PASS | ruff + mypy + complexity ≤10 committed; `make check` planned |
| III. Self-Improvement Loop | ✅ PASS | `docs/retrospective.md` artifact committed; `make check` single command |
| IV. Simplicity | ⚠️ JUSTIFIED | 3 sub-projects (backend, frontend, extension) — see Complexity Tracking |
| V. Observability | ✅ PASS | FastAPI structured logging (stdlib `logging`), timing on Oracle/Forge/Coach endpoints |

### Post-Phase 1 Re-check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Test-First | ✅ PASS | Contract tests defined in api-contracts.md; each user story has acceptance test |
| II. Code Quality | ✅ PASS | Function complexity budget held (services split into ≤40 line functions) |
| III. Self-Improvement | ✅ PASS | `make check` covers ruff + mypy + pytest for backend; `npm run lint && npm test` for frontend |
| IV. Simplicity | ✅ JUSTIFIED | 3-project structure justified below |
| V. Observability | ✅ PASS | Timing logs on all AI calls; FastAPI request logging middleware planned |

---

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| --------- | ---------- | ------------------------------------ |
| 3 sub-projects (backend, frontend, extension) | Backend = Python/FastAPI service; frontend = Next.js dashboard; extension = Chrome MV3 (cannot share Python runtime) | A single Python project cannot serve a browser dashboard UI or run as a Chrome extension; the three runtimes are fundamentally different |
| SQLite BLOB + file hybrid storage | Pages >500KB would bloat DB; pages <500KB are faster as BLOBs | All-on-disk breaks atomic record+snapshot consistency; all-in-DB slows queries on large pages |
| LaTeX subprocess in FastAPI | Polished PDF typography requires LaTeX; no pure-Python equivalent matches quality | ReportLab/WeasyPrint produce lower-quality output insufficient for a professional resume |

---

## Project Structure

### Documentation (this feature)

```text
specs/001-job-force-app/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   ├── api-contracts.md
│   ├── chrome-extension-contract.md
│   └── claude-skills-contract.md
└── tasks.md             ← Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
jobforce/
├── config.yaml                    # User config: search terms, companies, preferences
├── config.example.yaml            # Template with all fields documented
├── Makefile                       # make dev | make check | make seed
│
├── backend/                       # FastAPI service (Python 3.14)
│   ├── pyproject.toml
│   ├── Makefile                   # make check (ruff + mypy + pytest)
│   ├── jobforce/
│   │   ├── main.py                # FastAPI app factory, lifespan, middleware
│   │   ├── config.py              # pydantic-settings YAML loader
│   │   ├── db/
│   │   │   ├── engine.py          # async SQLAlchemy engine, WAL setup
│   │   │   ├── models.py          # ORM models (all entities)
│   │   │   ├── init.py            # create_all + alembic migrations
│   │   │   └── seed.py            # seed from config.yaml
│   │   ├── routers/
│   │   │   ├── ingest.py          # POST /api/ingest
│   │   │   ├── jobs.py            # GET/PATCH /api/jobs
│   │   │   ├── oracle.py          # POST /api/oracle/rank
│   │   │   ├── forge.py           # resume + PDF endpoints
│   │   │   ├── coach.py           # prep + mock interview endpoints
│   │   │   ├── dashboard.py       # GET /api/dashboard
│   │   │   ├── companies.py       # company detail + meeting notes
│   │   │   └── profile.py         # user profile endpoints
│   │   ├── services/
│   │   │   ├── scout.py           # dedup, parse, ingest logic
│   │   │   ├── oracle.py          # AI scoring via Anthropic SDK
│   │   │   ├── forge.py           # resume tailoring + LaTeX PDF
│   │   │   ├── coach.py           # web search + question generation
│   │   │   └── storage.py         # BLOB vs file routing for snapshots
│   │   └── templates/
│   │       └── resume.tex.j2      # Jinja2 LaTeX resume template
│   ├── data/
│   │   ├── jobforce.db            # SQLite database (gitignored)
│   │   └── pages/                 # Large HTML snapshots (gitignored)
│   └── tests/
│       ├── conftest.py            # async test client, temp DB fixtures
│       ├── contract/              # API contract tests (live test client)
│       │   ├── test_ingest.py
│       │   ├── test_jobs.py
│       │   ├── test_oracle.py
│       │   ├── test_forge.py
│       │   ├── test_coach.py
│       │   └── test_dashboard.py
│       ├── integration/           # service-layer integration tests
│       │   ├── test_scout_service.py
│       │   ├── test_forge_service.py
│       │   └── test_storage_service.py
│       └── unit/                  # pure unit tests
│           ├── test_config.py
│           └── test_db_models.py
│
├── frontend/                      # Next.js 14 dashboard (TypeScript)
│   ├── package.json
│   ├── next.config.ts             # API proxy to :8000 in dev
│   ├── tailwind.config.ts
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx         # Root layout, nav sidebar
│   │   │   ├── page.tsx           # / → HQ Dashboard
│   │   │   ├── jobs/page.tsx      # /jobs → Scout job board
│   │   │   ├── oracle/page.tsx    # /oracle → ranking view
│   │   │   ├── forge/page.tsx     # /forge → resume tailoring
│   │   │   ├── coach/page.tsx     # /coach → interview prep
│   │   │   └── companies/
│   │   │       └── [id]/page.tsx  # /companies/[id] → company detail
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── Sidebar.tsx    # Hero nav: Scout | Oracle | Forge | Coach | HQ
│   │   │   │   └── HeroCard.tsx   # Agent identity card with superhero theme
│   │   │   ├── jobs/
│   │   │   │   ├── JobTable.tsx
│   │   │   │   ├── StatusBadge.tsx
│   │   │   │   └── StatusTransitionModal.tsx
│   │   │   ├── dashboard/
│   │   │   │   ├── PipelineSummary.tsx
│   │   │   │   └── ActivityFeed.tsx
│   │   │   ├── forge/
│   │   │   │   ├── ResumeDiff.tsx
│   │   │   │   └── PDFDownloadButton.tsx
│   │   │   └── coach/
│   │   │       ├── QuestionCard.tsx
│   │   │       └── MockInterviewPanel.tsx
│   │   ├── lib/
│   │   │   ├── api.ts             # typed fetch helpers for all endpoints
│   │   │   └── types.ts           # TypeScript types matching API contracts
│   │   └── hooks/
│   │       ├── useJobs.ts
│   │       ├── useDashboard.ts
│   │       └── useProfile.ts
│   └── tests/
│       └── components/            # Jest + React Testing Library
│
├── chrome-extension/              # Chrome MV3 extension
│   ├── manifest.json
│   ├── background.js              # Service worker: receives message, POSTs to FastAPI
│   ├── content.js                 # Extracts page HTML + metadata, messages SW
│   ├── popup.html                 # Extension popup UI
│   ├── popup.js
│   ├── icons/                     # Jobforce shield icons (16, 48, 128px)
│   └── tests/
│       └── test_content_extraction.js   # Manual test script
│
└── .claude/
    └── skills/
        ├── speckit-scout-crawl.md     # Playwright MCP crawl skill
        ├── speckit-oracle-rank.md     # Oracle ranking skill
        ├── speckit-forge-tailor.md    # Forge resume + PDF skill
        └── speckit-coach-prep.md     # Coach web-search prep skill
```

**Structure Decision**: Multi-project layout — `backend/` (Python FastAPI),
`frontend/` (Next.js), `chrome-extension/` (MV3 JS). Three runtimes are
required and cannot be collapsed. `config.yaml` lives at root and is consumed
by the backend seed process. Claude Code skills live in `.claude/skills/`.
