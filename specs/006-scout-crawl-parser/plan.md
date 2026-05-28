# Implementation Plan: Scout Crawl Deterministic Parser

**Branch**: `006-scout-crawl-parser` | **Date**: 2026-05-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/006-scout-crawl-parser/spec.md`

## Summary

Replace the LLM-interpreted field extraction in the `/scout-crawl` skill with a single CLI tool that fetches a URL using the Python `playwright` library and parses the resulting HTML with a deterministic adapter registry mirroring the Chrome extension's two-layer architecture (generic + site-specific adapters keyed by hostname). The skill invokes one Bash command that handles both fetch and parse, returning JSON fields directly used in the ingest POST — no MCP browser tools, no AI inference of structured fields. Login-gated sites are handled separately.

## Technical Context

**Language/Version**: Python 3.12 (backend), markdown (skill)

**Primary Dependencies**: FastAPI (existing), BeautifulSoup4 + lxml + playwright (new additions), uv (existing runner)

**Storage**: No schema changes — `IngestPayload` and existing SQLite schema unchanged

**Testing**: pytest + pytest-asyncio (existing); new unit tests for parse module (parse logic tested against static HTML fixtures — no live browser needed in tests)

**Target Platform**: macOS/Linux (developer workstation, same as existing backend)

**Project Type**: Web service (backend) + Claude Code skill (markdown)

**Performance Goals**: Fetch + parse completes in < 10 seconds for any public job page

**Constraints**: No Anthropic SDK usage (Constitution VI); login-gated sites out of scope for this feature

**Scale/Scope**: Single-user local tool; ~10 site adapters expected over project lifetime

## Constitution Check

| Gate | Status | Notes |
|------|--------|-------|
| Test-first (Principle I) | PASS | Unit tests for parse module written before implementation |
| Code quality (Principle II) | PASS | ruff + mypy enforced; parse.py functions ≤ 40 lines each |
| Simplicity (Principle IV) | PASS | No new abstractions beyond the adapter dict pattern already in the Chrome extension |
| No AI SDK (Principle VI) | PASS | Parser is pure Python + BeautifulSoup; zero Anthropic SDK imports |
| Quality gates | PASS | All gates runnable via `make check` |

No violations. Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/006-scout-crawl-parser/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
└── tasks.md             ← Phase 2 output (from /speckit-tasks)
```

### Source Code Changes

```text
backend/
├── pyproject.toml                         # add beautifulsoup4, lxml, playwright deps
└── jobforce/
    ├── services/
    │   └── parse.py                       # NEW — adapter registry + parse_html()
    ├── cli/
    │   ├── __init__.py                    # NEW — make cli a package
    │   └── scout_fetch.py                 # NEW — fetch URL with playwright + parse + print JSON
    └── (existing files unchanged)

backend/tests/
└── unit/
    └── test_parse_service.py              # NEW — unit tests for parse.py (static HTML fixtures)

.claude/skills/scout-crawl/
└── SKILL.md                               # UPDATED — single Bash call replaces MCP browser dance
```

**Structure Decision**: Single backend project layout preserved. New `cli/` sub-package follows the existing `services/`, `routers/`, `db/` pattern. No new top-level directories.

## Implementation Details

### `backend/jobforce/services/parse.py`

Core module. Direct Python translation of `chrome-extension/content.js`:

```
GENERIC_ADAPTER = {
    "title":        fn using doc.select_one("h1") or doc.title
    "company_name": fn using data-company / .company-name / og:site_name meta
    "location":     fn using data-location / .job-location / job:location meta
    "description":  fn using [class*="description"] / [class*="job-desc"] / #job-description
    "role_type":    fn scanning body text for full-time / part-time / contract / internship
}

SITE_ADAPTERS = {
    "openai.com": {
        "company_name": () -> "OpenAI"
        "title":        doc.select_one("main h2")
        "location":     doc.select_one("main h2 + p, main h2 ~ p") or slug_to_location(url)
        "description":  doc.select_one("main article, main section")
        "compensation": first <p> in main starting with "$"
    }
}

def slug_to_location(pathname: str) -> str | None  # port of JS slugToLocation()
def run_adapter(adapter, doc, url) -> dict          # call each fn, catch errors
def merge(base, override) -> dict                   # override wins when non-null/non-empty
def parse_html(html: str, url: str) -> dict         # public entry point
```

### `backend/jobforce/cli/scout_fetch.py`

Single-command fetch + parse tool:
```
args: --url <str>
1. Launch Playwright (headless Chromium via async_playwright)
2. Navigate to URL, wait for networkidle
3. Grab document.documentElement.outerHTML
4. Call parse_html(html, url)
5. Print JSON to stdout
exits 0 on success, 1 on error (prints error to stderr)
```

### `SKILL.md` update (scout-crawl)

Replace all MCP browser tool steps + LLM field extraction with:

1. Run `cd backend && uv run python -m jobforce.cli.scout_fetch --url <URL>`
2. Parse stdout JSON → POST directly to ingest API
3. MCP Playwright tools are no longer used for field extraction

### Dependency addition

`pyproject.toml` `[project].dependencies`:
```
"beautifulsoup4>=4.12",
"lxml>=5.0",
"playwright>=1.44",
```

After install: `uv run playwright install chromium`

## Phase 0 Research Artifacts

- [research.md](research.md) — all decisions resolved, no NEEDS CLARIFICATION remaining

## Phase 1 Design Artifacts

- [data-model.md](data-model.md) — ParseResult struct and adapter registry design
- [quickstart.md](quickstart.md) — how to run parser and add new adapters
