# Research: Jobforce — Superhero Job Hunt Command Center

**Branch**: `001-job-force-app` | **Date**: 2026-05-27

## 1. FastAPI + SQLite

**Decision**: SQLAlchemy 2.0 async (`aiosqlite` driver), WAL journal mode, pool_size=5,
max_overflow=10, database file at `backend/data/jobforce.db`.

**Rationale**: Async prevents blocking on I/O; WAL mode enables concurrent readers
with a single writer, which suits the single-user local deployment. A dedicated
`data/` directory simplifies backup.

**Alternatives considered**: PostgreSQL (overkill for single-user local app),
SQLite with sync SQLAlchemy (would block async event loop).

**Key gotcha**: Exceeding ~10 concurrent connections without WAL causes lock
contention. Single-user load won't hit this, but crawl ingestion must serialize
bulk inserts.

---

## 2. Next.js 14 → FastAPI

**Decision**: Next.js API routes as proxy in development; direct fetch with Nginx
reverse proxy in production. `CORSMiddleware` on FastAPI with explicit allowed origins.
`concurrently` in package.json for local dev startup.

**Rationale**: Proxying via Next.js API routes eliminates CORS in dev and provides
a single request origin. Production Nginx at `/api/*` → FastAPI removes CORS
entirely.

**Alternatives considered**: Direct fetch in dev (requires CORS config maintenance);
separate Docker Compose service (adds complexity).

**Key gotcha**: FastAPI must handle OPTIONS preflight for non-simple requests
(POST with JSON body). `CORSMiddleware` handles this automatically — never use
`allow_origins=["*"]` for a local service with write access.

---

## 3. Chrome Extension — Manifest V3

**Decision**: MV3 extension with background service worker
(`background.service_worker`). Content script captures page HTML + metadata via
DOM APIs and messages the service worker via `chrome.runtime.sendMessage()`. Service
worker POSTs structured payload to local FastAPI (`http://localhost:8000/api/ingest`).

**Rationale**: MV3 is the current standard; service workers are required (background
pages deprecated). Message passing decouples content script from network I/O.

**Alternatives considered**: Content script making direct fetch to FastAPI (works but
mixes concerns and complicates CORS manifest permissions).

**Key gotcha**: Service workers are garbage-collected after ~30s idle. Persistent
state (e.g., auth tokens, last-crawled URL) MUST be stored in `chrome.storage.local`,
not in-memory globals.

---

## 4. Playwright MCP

**Decision**: Register via `claude mcp add playwright npx @playwright/mcp@latest`.
Claude Code skills invoke `mcp__playwright__navigate`, `mcp__playwright__get_text`,
and `mcp__playwright__evaluate` to navigate job board URLs, extract page content,
and return structured text to the FastAPI ingest endpoint.

**Rationale**: Playwright MCP exposes browser control as MCP tools callable directly
from Claude Code skills. It operates on the accessibility tree (not pixels), enabling
reliable structured content extraction without brittle CSS selectors.

**Alternatives considered**: Puppeteer (no MCP integration); direct HTTP fetch
(blocked by JS-rendered pages on modern job boards); selenium (slower, no MCP).

**Key gotcha**: Sites requiring login need a visible browser window and manual
auth step. Claude Code skill must pause and prompt user to log in, then resume.

---

## 5. LaTeX PDF Generation

**Decision**: Jinja2 templates with LaTeX-safe delimiters (`\VAR{}`, `\BLOCK{}`),
rendered to `.tex` then compiled via `latexmk -pdf` subprocess in the FastAPI
`/api/resume/export` endpoint. Output PDF streamed as file download.

**Rationale**: Jinja2 handles template logic (loops for work history, conditionals
for optional sections). `latexmk` handles multi-pass compilation and cleans temp
files. FastAPI streams the PDF bytes directly to the browser.

**Alternatives considered**: WeasyPrint/HTML→PDF (less precise typesetting);
ReportLab (programmatic, no template flexibility); pandoc (adds dep chain).

**Key gotcha**: `pdflatex` must be installed on the host. For containerized
deployment, use a `texlive-minimal` Docker base image. Temp files from failed
compilations must be cleaned up — wrap subprocess in try/finally.

---

## 6. SQLite Page Archiving

**Decision**: Store raw HTML as BLOB in a `page_snapshots` table for pages ≤500KB;
store path reference in `page_snapshots.file_path` for larger pages with HTML files
in `backend/data/pages/`. Threshold configurable in `config.yaml`.

**Rationale**: SQLite BLOBs are 35% faster than filesystem for <100KB reads and
keep the archive atomic with the structured record. Pages >500KB (rare for job
listings) are stored on disk to avoid DB bloat.

**Alternatives considered**: All-on-disk (breaks atomicity, path drift risk);
all-in-DB (slows queries on large snapshots).

**Key gotcha**: External file paths can break on volume remounts. Implement a
`storage.verify_integrity()` check on startup that cross-references DB path refs
against filesystem.

---

## 7. YAML Config Seeding

**Decision**: `pydantic-settings` v2 with `yaml_file="config.yaml"`, Pydantic models
for `SearchConfig`, `CompanyConfig`, `DatabaseConfig`. A `seed_from_config()`
function runs at FastAPI startup (idempotent — skips existing records).

**Rationale**: Pydantic validates the YAML schema at startup with clear error
messages. Idempotent seeding means the file can be re-run or updated without
duplicating data.

**Alternatives considered**: Plain PyYAML (no validation, silent failures);
Dynaconf (overkill for a single config file).

**Key gotcha**: `pydantic-settings` requires `pydantic-settings[yaml]` extra
(`pip install pydantic-settings[yaml]`). Missing YAML fields that are required
crash at startup — desired behavior, but document all required fields in comments
in the example `config.yaml`.

---

## 8. Claude Code Orchestration

**Decision**: Claude Code skills (`.claude/skills/`) orchestrate multi-agent
workflows: Scout crawl missions (Playwright MCP + Chrome ext ingest), Oracle ranking
(AI scoring via Anthropic API), Forge resume tailoring + LaTeX export, Coach
web-search interview prep. Each skill is a Markdown prompt file invoking MCP tools
and/or FastAPI endpoints.

**Rationale**: Claude Code's skill system allows new agent capabilities to be added
as `.md` files without code changes to the core app. MCP servers (Playwright, custom
Jobforce MCP) expose tools Claude can call directly.

**Alternatives considered**: LangChain/LangGraph (heavy framework, complex debugging);
direct Python agent loops (no natural language orchestration, harder to extend).

**Key gotcha**: Skills are stateless Markdown prompts — persistent context (current
job target, session state) must be passed explicitly via the FastAPI backend or
`feature.json`-style state files.
