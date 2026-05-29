# Implementation Plan: Company Careers Search Skill

**Branch**: `009-company-careers-search` | **Date**: 2026-05-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/009-company-careers-search/spec.md`

## Summary

Add a `/scout-companies` Claude Code skill that reads `search.target_companies` from `config.yaml`, visits each company's careers page using Playwright MCP, extracts individual job listing URLs, and hands each URL off to the existing `scout_fetch` CLI → `POST /api/ingest` pipeline (identical to `/scout-crawl`). Also extends `CompanyConfig` with an optional `careers_url` field for ATS-hosted pages. No new backend endpoints are needed.

## Technical Context

**Language/Version**: Python 3.12 (backend config extension); Markdown skill definition only for the skill itself

**Primary Dependencies**: Playwright MCP (browser navigation in skill), existing `jobforce.cli.scout_fetch`, existing `POST /api/ingest`

**Storage**: No new storage — existing `job_listings` table via existing ingest path

**Testing**: pytest + pytest-asyncio (config model unit test); skill is tested manually via invocation

**Target Platform**: Local dev (`cd backend && make dev`); skill runs in Claude Code

**Project Type**: Claude Code skill + minimal backend config extension

**Performance Goals**: No latency constraints — human-triggered, interactive

**Constraints**: Zero `anthropic` SDK imports (Constitution VI). Skill uses Playwright MCP only, never the Anthropic SDK.

**Scale/Scope**: Single-user personal tool; typically 2–10 target companies

## Constitution Check

| Principle | Status | Notes |
| --------- | ------ | ----- |
| I. Test-First | ✅ | Unit test for `CompanyConfig.careers_url` field written before implementation |
| II. Code Quality | ✅ | Config change is one field addition; ruff/mypy clean |
| III. Self-Improvement Loop | ✅ | No regression patterns introduced |
| IV. Simplicity & Clarity | ✅ | Skill delegates to existing `scout_fetch`; no new abstractions |
| V. Observability | ✅ | Skill prints per-company progress and final summary |
| VI. Cost-Conscious AI | ✅ | No `anthropic` SDK; all browser work via Playwright MCP subscription |

**AI SDK Gate**: `grep -r "import anthropic" backend/` → zero results ✅

## Project Structure

### Documentation (this feature)

```text
specs/009-company-careers-search/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (affected files)

```text
backend/
└── jobforce/
    └── config.py              # CompanyConfig: add optional careers_url field

backend/tests/unit/
└── test_config.py             # Add test: CompanyConfig accepts careers_url

.claude/skills/
└── scout-companies/
    └── SKILL.md               # New skill definition

config/
└── config.example.yaml        # Add careers_url to target_companies example
```

## Complexity Tracking

No constitution violations. Change is additive only.

---

## Phase 0: Research

### Decision: Skill architecture — Playwright MCP for discovery, scout_fetch CLI for parsing

**Decision**: The skill uses Playwright MCP to navigate careers pages and extract job listing URLs. Each discovered URL is passed to `cd backend && uv run python -m jobforce.cli.scout_fetch --url <url>`, then the JSON output is POSTed to `POST /api/ingest` — identical to the `/scout-crawl` flow.

**Rationale**: Reuses the entire proven parse → ingest pipeline. The only new work is the careers page navigation and link extraction, which is inherently judgment-based (page layouts vary) and well-suited to Claude Code + Playwright MCP.

**Alternatives considered**: A backend CLI search runner was considered but rejected — it would require maintaining site-specific crawlers in Python and couldn't leverage Claude's judgment for extracting job links from varied page layouts.

---

### Decision: Career page discovery strategy (no careers_url set)

**Decision**: When `careers_url` is not set, construct candidate URLs from the company `domain` field using a fixed list of common paths tried in order: `/careers`, `/jobs`, `/openings`, `/join-us`. Navigate to each; the first that loads and contains job-like links (anchor tags with text patterns matching role keywords) is used. If none succeed, report "careers page not found" for that company and continue.

**Rationale**: A fixed path list covers ~80% of company career pages without requiring AI URL guessing. Setting `careers_url` is the escape hatch for ATSs and non-standard paths. Simple and predictable.

**Alternatives considered**: Using Google "site:domain.com careers" search was considered but adds external dependency and rate-limit risk.

---

### Decision: Job link extraction from careers page

**Decision**: Claude (via Playwright MCP) identifies anchor tags on the careers page whose `href` values look like individual job posting URLs (contain path segments like `/jobs/`, `/roles/`, `/positions/`, numeric IDs, or job-title-like slugs) vs. navigation/filter links. Extract all candidate URLs, deduplicate, and process each.

**Rationale**: Job board page structures vary too widely for regex; Claude's judgment is the right tool here. This is the key value-add of the skill pattern vs. a backend crawler.

**Alternatives considered**: CSS selector heuristics were considered but are too brittle across different ATS platforms.

---

### Decision: `careers_url` as optional field on `CompanyConfig`

**Decision**: Add `careers_url: str = ""` to the existing `CompanyConfig` Pydantic model in `backend/jobforce/config.py`. Empty string means "auto-discover".

**Rationale**: Minimal change to existing model. Consistent with how `domain` is handled (also defaults to empty string). No migration needed — SQLite `companies` table is not affected; this is config-only.

**Alternatives considered**: A separate `ats_url` field was considered but `careers_url` is more general and covers all cases (ATS-hosted or custom).

---

See [research.md](research.md) for full findings.

## Phase 1: Design & Contracts

See [data-model.md](data-model.md) and [contracts/](contracts/) for entity and skill interface details.
