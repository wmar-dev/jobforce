# Quickstart: Verifying Coverage for This Feature

## Baseline (before any change)

```bash
cd backend
uv run pytest --cov=jobforce.routers.jobs --cov=jobforce.services.coach --cov-report=term-missing tests/
```

Current reported coverage: `routers/jobs.py` 62%, `services/coach.py` 48%.

## Step 1 — apply the coverage config fix (research.md Decision 1)

Add `concurrency = ["greenlet", "thread"]` to `[tool.coverage.run]` in `backend/pyproject.toml`:

```toml
[tool.coverage.run]
omit = ["tests/*"]
concurrency = ["greenlet", "thread"]
```

Re-run the same command above with no test changes. Expected new baseline: `routers/jobs.py` ~92%,
`services/coach.py` ~76%. If these numbers don't move, stop and re-investigate before writing any new tests —
it means the tracer fix didn't take effect (check `coverage --version` supports `concurrency`, and that
`.coverage` cache was cleared: `rm -f backend/.coverage`).

## Step 2 — add the targeted tests

Extend `backend/tests/contract/test_jobs.py`, `backend/tests/contract/test_coach.py`, and add
`backend/tests/services/test_coach.py` per the functional requirements in spec.md and the remaining
uncovered lines below (re-check exact line numbers after Step 1, since line numbers shift slightly if any
other edit touches these files first):

```bash
cd backend
uv run pytest --cov=jobforce.routers.jobs --cov=jobforce.services.coach --cov-report=term-missing tests/ -q \
  | grep -E "jobs\.py|coach\.py"
```

## Step 3 — full quality gate

```bash
cd backend
make check   # ruff lint + ruff format --check, mypy strict, pytest with coverage
```

## Step 4 — re-verify the standing invariant

```bash
grep -r "import anthropic" backend/   # must return zero results outside services/coach.py — and coach.py
                                       # itself must have zero, since the anthropic SDK was already removed
                                       # in feature 011
```

## Success check

`SC-001`/`SC-002` are met once the `term-missing` report shows both files at ≥85%. `SC-004` is met once
`make check` passes cleanly with no reduction in any other module's coverage.
