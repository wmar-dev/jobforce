---
name: housekeeping
description: Periodic maintenance pass over the repo — updates backend (uv) and frontend (npm) dependencies within their existing declared version ranges, flags any available major-version bumps for manual review instead of applying them, runs `make check` (lint + typecheck + test across backend and frontend), flags notable test coverage gaps for a follow-up pass, and verifies the "no `anthropic` SDK import outside coach.py" invariant from CLAUDE.md. Use when the user wants to update dependencies, do routine maintenance, or run a periodic health check on the repo.
argument-hint: (none)
user-invocable: true
---

# Housekeeping

Run this periodically (e.g. monthly) to keep dependencies current and catch drift, without silently pulling in breaking changes.

## Step 1: Confirm a clean working tree

```bash
git status --porcelain
```

If this prints anything, stop and tell the user: uncommitted changes exist, commit or stash them first since this skill is about to modify lockfiles (`uv.lock`, `package-lock.json`).

## Step 2: Survey outdated packages

```bash
cd backend && uv pip list --outdated
cd frontend && npm outdated   # exits 1 when packages are outdated — that's expected, not a failure
```

For each outdated package, classify it:

- **Safe (same major version)** — the latest available version has the same major version number as what's currently resolved. These are backward-compatible per semver and safe to bump automatically.
- **Needs manual review (major bump)** — latest available crosses a major version boundary (e.g. `14.x` → `15.x`, `0.x` → `1.x` for pre-1.0 packages, `18.x` → `19.x`). Do **not** apply these automatically — breaking changes are likely. Collect these into a list to report at the end instead.

Note: backend `pyproject.toml` dependencies are declared as open-ended lower bounds (`fastapi>=0.111`), so `uv lock --upgrade` alone could silently jump a major version. Always upgrade backend packages one at a time by name (Step 3), never with a blanket `uv lock --upgrade`.

## Step 3: Apply the safe updates

**Backend** — for each "safe" package from Step 2:

```bash
cd backend && uv lock --upgrade-package <package-name>
```

Then sync:

```bash
cd backend && uv sync --extra dev
```

**Frontend** — `npm update` only ever moves within the semver ranges already declared in `package.json` (e.g. `^15.5.18` will update within `15.x` but never jump to `16.x`), so it's safe to run unconditionally:

```bash
cd frontend && npm update
```

Do not edit `package.json`/`pyproject.toml` version constraints yourself for major bumps — that's a deliberate decision for the user to make, not something to apply during routine housekeeping.

## Step 4: Run quality gates

```bash
make check   # backend: ruff lint + mypy + pytest; frontend: ESLint + Jest
```

If anything fails, stop here — report the failure output and do not proceed to committing. A housekeeping pass should never leave the repo in a broken state.

## Step 5: Flag test coverage gaps

`make check` already ran backend tests with coverage (`--cov=jobforce --cov-report=term-missing`, configured in `backend/pyproject.toml`). Skim that output for:

- Modules with notably low coverage or large blocks of missing lines — especially in `backend/jobforce/services/` and `backend/jobforce/routers/` (business logic), not boilerplate like `db/models.py`.
- Any package bumped in Step 3 whose touched code has thin coverage — a good sign the upgrade path itself is under-tested.

Frontend has no coverage reporting configured (`npm test` runs `jest --passWithNoTests`, no `--coverage` flag). As a lightweight substitute, check whether files under `frontend/src/components/` and `frontend/src/hooks/` have a colocated or `__tests__` test file at all — skip trivial presentational components.

This is a lightweight flag, not a full coverage audit: only note real gaps (0%/near-0% coverage, or business logic with no test file at all), and don't write the tests yourself — collect them to report in Step 7 for the user to decide on a follow-up pass. Coverage gaps need judgment about what's worth testing, which is out of scope for a routine dependency-maintenance run.

## Step 6: Verify the AI-in-skills invariant

Per CLAUDE.md, all AI reasoning except Coach must live in Claude Code skills, not the backend:

```bash
grep -rn "import anthropic" backend/
```

Expected: zero matches, or matches only in `backend/jobforce/services/coach.py`. If any other file imports `anthropic`, flag it clearly — it means the skill-driven AI architecture has regressed.

## Step 7: Report and hand off

Summarize:

- **Applied**: each package bumped, with old → new version.
- **Flagged for manual review**: each major-version bump available, with current → latest version, left for a dedicated upgrade pass rather than applied here.
- **Quality gates**: pass/fail.
- **Test coverage gaps**: any modules/files flagged in Step 5, or "none notable" if the pass was clean.
- **Invariant check**: pass/fail (with offending file(s) if it failed).

Do not commit automatically. Ask the user whether to commit the lockfile/dependency changes — following the project's normal commit convention (only commit when asked).
