# Research: Oracle SDK-Free Job Ranking

**Feature**: `005-oracle-no-sdk` | **Date**: 2026-05-27

## Decision Log

### 1. How Claude Code performs the ranking

**Decision**: The `/oracle-rank` Claude Code skill fetches job and profile data
from the backend REST API, reasons about fit inline (Claude Code's own context
window is the AI), and writes scores back via `PATCH /api/jobs/{id}`.

**Rationale**: Claude Code is already the execution environment — no subprocess,
no IPC, no extra runtime needed. The skill reads JSON from `GET /api/jobs` and
`GET /api/profile`, reasons over each job, and PATCHes the result. This is
identical to how `site-adapter-update.md` and `scout-crawl.md` work.

**Alternatives considered**:
- `claude -p "..."` subprocess from the backend: adds process spawning,
  complicates async FastAPI, still requires the backend to trigger it.
- Separate daemon process polling the DB: over-engineered for a local dev tool.
- Keep SDK but gate behind a flag: still violates Constitution Principle VI.

---

### 2. What happens to `POST /api/oracle/rank`

**Decision**: Keep the endpoint but make it a stub that returns an informative
error explaining the new workflow. Do not delete it — the frontend and tests
both reference it.

**Rationale**: Deleting it would break existing contract tests and the frontend
at the same time. A stub with a clear 503 or 501 response is safer and easier
to reverse. The frontend replaces the button with an instruction panel (US3)
so the endpoint is never triggered from the UI after this change.

**Alternatives considered**:
- Delete the endpoint entirely: requires simultaneous frontend + test changes,
  higher risk.
- Keep it functional with a mock ranker: defeats the purpose.

---

### 3. Score write path

**Decision**: Reuse the existing `PATCH /api/jobs/{id}` endpoint, extending
`JobPatchRequest` to accept `fit_score`, `fit_scored`, `fit_confidence`, and
`fit_rationale`. No new endpoint needed.

**Rationale**: The `PATCH /jobs/{id}` endpoint was already added in feature 004
(commit `df47a0f`). Extending it is simpler than adding `POST /oracle/score/{id}`.
The contract test for the write path tests `PATCH /jobs/{id}` directly.

**Alternatives considered**:
- Dedicated `POST /oracle/score/{job_id}`: more REST-idiomatic but adds an
  endpoint for no additional capability.

---

### 4. `oracle.py` service layer after SDK removal

**Decision**: Keep `_build_profile_text`, `_confidence_label`, `_build_ranking_prompt`,
and `_parse_ranking_response` as pure helper functions (no I/O). Delete
`rank_jobs` (the async function that called the SDK). The router's
`post_rank` becomes a stub returning 501.

**Rationale**: The helpers are useful documentation and may be referenced by
the skill for prompt format consistency. Keeping them costs nothing and avoids
deleting tested logic.

---

### 5. Frontend change

**Decision**: Replace the "Run Oracle Ranking" button with a static instruction
panel: `Run /oracle-rank in Claude Code to score your jobs`. Keep the results
display section — it reads from the existing `GET /api/oracle/rank/{id}` calls
which still work.

**Rationale**: The results display is independent of how scores are generated.
Removing the button without removing the results panel preserves the ability
to view previously-ranked jobs. The instruction panel tells the user exactly
what to do.

---

### 6. pyproject.toml

**Decision**: Remove `"anthropic>=0.28"` from `[project].dependencies` in
`backend/pyproject.toml`. No replacement dependency needed.

**Rationale**: Nothing in the remaining code imports `anthropic` after the
service rewrite. Leaving it in the dependency list would be misleading and
keep the package installed unnecessarily.
