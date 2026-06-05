# Implementation Plan: Hacker News "Who's Hiring" Parser

**Branch**: `012-hn-whos-hiring-parser` | **Date**: 2026-06-05 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/012-hn-whos-hiring-parser/spec.md`

## Summary

Add deterministic, LLM-free parsing support for `news.ycombinator.com` job listings. Two deliverables: (1) a `news.ycombinator.com` site adapter in `parse.py` that extracts structured fields from a single HN comment, and (2) a `hn_thread` CLI module that accepts a "Who's Hiring" thread URL and outputs individual comment URLs as JSON — enabling `/scout-companies` to bulk-ingest an entire monthly thread without any in-skill HTML parsing or LLM token spend.

## Technical Context

**Language/Version**: Python 3.12 (matches project)

**Primary Dependencies**: BeautifulSoup4 + lxml (already in use in `parse.py`), markdownify (already in use), httpx or stdlib urllib (for `hn_thread` CLI HTTP fetch — no Playwright needed, HN is server-rendered)

**Storage**: SQLite via existing `ingest_listing` path — no schema changes

**Testing**: pytest with static HTML fixtures (mirrors `tests/unit/test_parse_service.py` pattern)

**Target Platform**: Local dev (macOS/Linux), same as rest of backend

**Project Type**: CLI module + site adapter (library extension)

**Performance Goals**: Full thread (50 comments) ingested in under 60 seconds (SC-004)

**Constraints**: Zero LLM calls in parse path (SC-003, Constitution Principle VI); no new dependencies unless strictly required

**Scale/Scope**: ~400–600 top-level comments in a monthly HN "Who's Hiring" thread; single-comment parse is O(1) HTML parse

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle             | Status  | Notes                                                                                 |
| --------------------- | ------- | ------------------------------------------------------------------------------------- |
| I. Test-First         | ✅ PASS | All new code gated on failing tests first (fixtures + unit tests before adapter code) |
| II. Code Quality      | ✅ PASS | ruff + mypy in `make check`; functions will stay ≤40 lines                            |
| III. Self-Improvement | ✅ PASS | `make check` covers all gates                                                         |
| IV. Simplicity        | ✅ PASS | No new abstractions; adapter follows existing pattern exactly                         |
| V. Observability      | ✅ PASS | `logger.warning` on parse failures, consistent with existing adapters                 |
| VI. Cost-Conscious AI | ✅ PASS | Zero `anthropic` imports; pure BeautifulSoup + regex                                  |

No violations. Complexity Tracking table not required.

## Project Structure

### Documentation (this feature)

```text
specs/012-hn-whos-hiring-parser/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code

```text
backend/
├── jobforce/
│   ├── cli/
│   │   └── hn_thread.py          # NEW: thread URL → comment URLs JSON
│   └── services/
│       └── parse.py              # MODIFIED: add HN site adapter + _hn_* helpers
└── tests/
    ├── fixtures/
    │   ├── hn_comment_pipe.html  # NEW: pipe-delimited first-line fixture
    │   ├── hn_comment_prose.html # NEW: free-form first-line fixture
    │   └── hn_thread.html        # NEW: thread page fixture (subset of comments)
    └── unit/
        └── test_parse_service.py # MODIFIED: add HN adapter test cases
        └── test_hn_thread.py     # NEW: tests for hn_thread CLI module
```

`.claude/skills/scout-companies/SKILL.md` — MODIFIED: add HN thread detection step

## Complexity Tracking

No violations to justify.
