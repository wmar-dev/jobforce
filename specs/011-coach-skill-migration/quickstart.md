# Quickstart: Coach Skill Migration

## What's changing

The backend coach service no longer calls the Anthropic SDK. The `/coach-prep` skill now generates questions using in-context Claude reasoning (Pro subscription) and POSTs the result to the backend for storage. The frontend is unchanged.

## Dev setup (no changes required)

```bash
make dev          # backend :8000 + frontend :3000 as normal
```

## Testing the new flow

```bash
# 1. Start backend
cd backend && make dev

# 2. In Claude Code, generate a prep pack
/coach-prep 42    # replace 42 with a real job ID

# 3. Open the web UI to confirm the session appears
open http://localhost:3000/coach
```

## Verifying the SDK is gone

```bash
grep -r "import anthropic" backend/   # must return zero results
cd backend && make check              # lint + typecheck + tests must all pass
```

## Key files changed

| File | Change |
| ---- | ------ |
| `backend/pyproject.toml` | Remove `anthropic>=0.105.0` |
| `backend/jobforce/services/coach.py` | Remove SDK calls; stub answer eval |
| `backend/jobforce/routers/coach.py` | `PrepRequest` gains required `questions` field |
| `backend/tests/contract/test_coach.py` | Remove mock patches; test real DB writes |
| `.claude/skills/coach-prep/SKILL.md` | Rewrite: in-context generation + POST to backend |
