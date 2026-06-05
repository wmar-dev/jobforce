# Tasks: HN "Who's Hiring" Parser

**Input**: Design documents from `specs/012-hn-whos-hiring-parser/`

**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/hn_thread_cli.md ✅

**Tests**: Included — the spec requires unit tests with static HTML fixtures as the primary correctness gate (FR-008, SC-005).

**Organization**: Tasks grouped by user story. US1 and US3 are both P1 and share the adapter; they are implemented together in Phase 3. US2 (bulk ingest via skill) is P2 and depends on Phase 3 completing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no shared dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm fixtures and test infrastructure exist. No new dependencies needed — BeautifulSoup4, lxml, markdownify, and httpx are already installed.

- [x] T001 Verify HTML fixtures exist in `backend/tests/fixtures/` — `hn_comment_pipe.html`, `hn_comment_prose.html`, `hn_thread.html` must all be present and non-empty (check-only, no code change)
- [x] T002 Confirm `backend/jobforce/cli/` directory exists; create it with an empty `__init__.py` if absent

**Checkpoint**: Fixtures present, CLI package directory exists — implementation can begin.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Establish the test scaffolding files that all story phases will fill in. Tests are written before implementation (Constitution Principle I).

- [x] T003 [P] Create failing test file `backend/tests/unit/test_parse_service_hn.py` with two placeholder test stubs: `test_hn_pipe_comment_extracts_fields` and `test_hn_prose_comment_extracts_company` — import the fixture loader from the existing `test_parse_service.py` pattern, assert `False` so they fail
- [x] T004 [P] Create failing test file `backend/tests/unit/test_hn_thread.py` with one placeholder test stub: `test_hn_thread_extracts_comment_urls` — assert `False` so it fails

**Checkpoint**: `uv run pytest tests/unit/test_parse_service_hn.py tests/unit/test_hn_thread.py` → 3 failures, 0 errors — scaffolding confirmed.

---

## Phase 3: User Stories 1 & 3 — HN Adapter + Structured Extraction (Priority: P1) 🎯 MVP

**Goal**: A `news.ycombinator.com` site adapter in `parse.py` that extracts structured fields from a single HN comment page. Covers FR-001 through FR-008.

**Independent Test**: `uv run pytest tests/unit/test_parse_service_hn.py -v` passes; `uv run pytest tests/unit/test_parse_service.py -v` shows no regressions.

### Tests for US1 & US3

- [x] T005 [P] [US1] Write test `test_hn_pipe_comment_extracts_fields` in `backend/tests/unit/test_parse_service_hn.py` — load `hn_comment_pipe.html`, call `parse_html(html, url)` where `url` is an `item?id=` comment URL, assert `company_name`, `title`, `location`, `role_type`, `description` are all populated
- [x] T006 [P] [US1] Write test `test_hn_prose_comment_extracts_company` in `backend/tests/unit/test_parse_service_hn.py` — load `hn_comment_prose.html`, call `parse_html(html, url)`, assert `company_name` is non-null, `title` is null, `description` is non-null markdown
- [x] T007 [P] [US3] Write test `test_hn_pipe_role_type_detection` in `backend/tests/unit/test_parse_service_hn.py` — use the pipe fixture and assert `role_type == "full-time"` given the known fixture content
- [x] T008 [P] [US3] Write test `test_hn_pipe_missing_pipe_fallback` in `backend/tests/unit/test_parse_service_hn.py` — construct minimal HTML with a prose first line (no `|`), assert `title` is null and `company_name` equals the first token of the first line

Run: `uv run pytest tests/unit/test_parse_service_hn.py -v` → all 4 tests FAIL (expected at this stage).

### Implementation for US1 & US3

- [x] T009 [US1] Add `_hn_extract_commtext(soup) -> Tag | None` helper in `backend/jobforce/services/parse.py` — select `.commtext` from `.fatitem` layout; return None if absent or class includes `cdd`/`cdf`
- [x] T010 [US1] Add `_hn_first_line(commtext: Tag) -> str` helper in `backend/jobforce/services/parse.py` — return the first non-empty line of the comment's plain text
- [x] T011 [US3] Add `_hn_parse_pipe(first_line: str) -> dict` helper in `backend/jobforce/services/parse.py` — split on `|`, map token[0]→company_name, token[1]→title, token[2]→location; scan all tokens for role_type keywords (`full-time`, `part-time`, `contract`, `intern`); return dict with those keys (values may be None)
- [x] T012 [US3] Add `_hn_role_type_from_tokens(tokens: list[str]) -> str | None` helper in `backend/jobforce/services/parse.py` — scan lowercased tokens for known keywords; return canonical value or None
- [x] T013 [US1] Add `_parse_hn(html: str, url: str) -> dict` adapter function in `backend/jobforce/services/parse.py` — orchestrates: parse HTML → extract commtext → extract first line → branch on `|` presence → call `_hn_parse_pipe` or extract company from first token → convert commtext HTML to markdown via `markdownify` → return full parse dict
- [x] T014 [US1] Register HN adapter in the `parse_html` routing block in `backend/jobforce/services/parse.py` — add `elif "news.ycombinator.com" in url: return _parse_hn(html, url)` before the generic fallback
- [x] T015 [US1] Run `uv run pytest tests/unit/test_parse_service_hn.py -v` → all 4 tests must PASS
- [x] T016 [US1] Run `uv run pytest tests/unit/test_parse_service.py -v` → zero regressions (SC-005)
- [x] T017 [US1] Run `uv run mypy backend/jobforce/services/parse.py` → zero new type errors

**Checkpoint**: HN adapter fully working. A single HN comment URL can be parsed and ingested via the existing `scout_fetch` CLI with no changes to that CLI.

---

## Phase 4: User Story 2 — `hn_thread` CLI + `/scout-companies` Integration (Priority: P2)

**Goal**: A checked-in `hn_thread` CLI module that extracts comment URLs from an HN thread page, plus an updated `/scout-companies` skill that invokes it. Covers FR-009 and FR-010.

**Independent Test**: `python -m jobforce.cli.hn_thread "https://news.ycombinator.com/item?id=48357725"` (live) returns a JSON array of comment URLs; `uv run pytest tests/unit/test_hn_thread.py -v` passes against the static fixture.

### Tests for US2

- [x] T018 [US2] Write test `test_hn_thread_extracts_comment_urls` in `backend/tests/unit/test_hn_thread.py` — load `hn_thread.html` as a string, call the internal `_extract_comment_urls(html, base_url)` function (not the CLI entry-point), assert result is a non-empty list of strings each matching `https://news.ycombinator.com/item?id=`
- [x] T019 [US2] Write test `test_hn_thread_skips_dead_comments` in `backend/tests/unit/test_hn_thread.py` — construct minimal HTML with one live and one dead (`cdd` class) comment row, assert dead comment URL is absent from result

Run: `uv run pytest tests/unit/test_hn_thread.py -v` → both tests FAIL.

### Implementation for US2

- [x] T020 [US2] Create `backend/jobforce/cli/hn_thread.py` — implement `_extract_comment_urls(html: str, base_url: str) -> list[str]`: parse `tr.athing.comtr` with `td.ind[indent="0"]`, skip rows whose `.commtext` has class `cdd` or `cdf`, build `https://news.ycombinator.com/item?id=<id>` URLs
- [x] T021 [US2] Add `_fetch_thread_html(url: str) -> str` to `backend/jobforce/cli/hn_thread.py` — plain HTTP GET with `User-Agent: Mozilla/5.0` (use `urllib.request` — no new deps); raise on non-200 with descriptive message
- [x] T022 [US2] Add `__main__` entry-point to `backend/jobforce/cli/hn_thread.py` — validate the URL argument starts with `https://news.ycombinator.com/`, call `_fetch_thread_html`, call `_extract_comment_urls`, print JSON array to stdout; print progress/error to stderr; exit 1 on failure
- [x] T023 [US2] Run `uv run pytest tests/unit/test_hn_thread.py -v` → both tests must PASS
- [x] T024 [US2] Run `uv run mypy backend/jobforce/cli/hn_thread.py` → zero type errors
- [x] T025 [US2] Update `.claude/skills/scout-companies/SKILL.md` — add a detection step: "If `careers_url` contains `news.ycombinator.com`, run `python -m jobforce.cli.hn_thread <careers_url>` to get comment URLs as JSON, then call `scout_fetch --url <url>` for each — skip the Playwright careers-page step for this entry"

**Checkpoint**: `python -m jobforce.cli.hn_thread <thread_url>` works end-to-end. `/scout-companies` updated with HN branch.

---

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Quality gates, logging, and documentation.

- [x] T026 [P] Run full backend quality gate `cd backend && make check` → all linting, type-checking, and tests pass (note: pre-existing dashboard.py format issue unrelated to this feature)
- [x] T027 [P] Add `logger.warning("hn adapter: commtext not found for %s", url)` in `_parse_hn` when `.commtext` is absent — consistent with existing adapter error handling in `parse.py`
- [x] T028 Smoke-test live: run `python -m jobforce.cli.hn_thread "https://news.ycombinator.com/item?id=48357725" | head -c 200` and confirm JSON output (verifies User-Agent header and HTML parsing against real HN)
- [x] T029 [P] Verify invariant: `grep -r "import anthropic" backend/` → zero results (SC-003)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — creates failing test stubs; BLOCKS Phase 3 & 4
- **Phase 3 (US1 + US3)**: Depends on Phase 2 — P1 priority, implement first
- **Phase 4 (US2)**: Depends on Phase 3 being complete (uses the adapter) — P2 priority
- **Phase 5 (Polish)**: Depends on Phases 3 & 4

### User Story Dependencies

- **US1 + US3 (P1)**: Adapter + structured extraction — no dependencies between them; implemented together in Phase 3
- **US2 (P2)**: `hn_thread` CLI + skill update — depends on the adapter (Phase 3) being importable but not on its tests passing; can start in parallel with T015–T017 in practice

### Within Each Phase

- T005–T008 (tests) can all run in parallel — different test functions in the same file
- T009–T013 (helpers) should be written in dependency order: extract → first_line → role_type → parse_pipe → adapter
- T020–T022 (`hn_thread.py`) written sequentially: internal functions before entry-point

---

## Parallel Execution Examples

### Phase 3 — Write all 4 tests at once:

```
T005: test_hn_pipe_comment_extracts_fields
T006: test_hn_prose_comment_extracts_company
T007: test_hn_pipe_role_type_detection
T008: test_hn_pipe_missing_pipe_fallback
```

### Phase 4 — Write both tests at once:

```
T018: test_hn_thread_extracts_comment_urls
T019: test_hn_thread_skips_dead_comments
```

---

## Implementation Strategy

### MVP (Phase 1 + 2 + 3 only)

1. Confirm fixtures (T001–T002)
2. Write failing tests (T003–T004)
3. Write adapter tests (T005–T008) — fail
4. Implement adapter helpers (T009–T013) + register route (T014)
5. Tests pass (T015–T017)
6. **STOP and VALIDATE**: single-comment ingest working, all US1/US3 acceptance criteria met

### Full Feature (adds Phase 4)

7. Write `hn_thread` tests (T018–T019) — fail
8. Implement CLI (T020–T022)
9. Tests pass (T023–T024)
10. Update scout-companies skill (T025)
11. Polish + quality gates (T026–T029)

---

## Notes

- [P] tasks = different files, no shared state — safe to parallelize
- Test stubs in Phase 2 must assert `False` so `make check` shows failures before implementation
- All `parse.py` helpers must be under 40 lines each (plan.md constraint)
- `hn_thread.py` uses `urllib.request` — no new pip dependencies
- Commit after each checkpoint to preserve working state
