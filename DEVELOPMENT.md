# Development

This file covers tooling for maintaining the Jobforce repo itself. For day-to-day usage of the app, see [README.md](README.md); for architecture and coding conventions, see [CLAUDE.md](CLAUDE.md).

## Maintainer-only skills

These run inside Claude Code but aren't part of the job-search workflow — they keep the repo itself healthy. They're not listed in the README's Usage section since they're for whoever maintains this repo, not end users of the app.

| Skill | Purpose |
| --- | --- |
| `/housekeeping` | Periodic maintenance pass: updates backend (`uv`) and frontend (`npm`) dependencies within their existing declared version ranges, flags available major-version bumps for manual review instead of applying them, runs `make check`, and verifies the "no `anthropic` SDK import outside `coach.py`" invariant from CLAUDE.md. Run this periodically (e.g. monthly). |
| `/token-audit` | Analyzes a Claude Code session transcript to see what drove token/context usage and suggests concrete efficiency changes for future sessions. |

## Dependency upgrade policy

- Routine same-major-version bumps are safe to apply via `/housekeeping` — it does this automatically.
- Major-version bumps (e.g. Next 15 → 16, React 18 → 19) are **not** applied automatically, even when `/housekeeping` finds them available. Treat each as its own deliberate task: read the changelog/migration guide, apply it on a branch, and run `make check` plus manual smoke-testing before merging.
- Backend `pyproject.toml` dependencies use open-ended lower bounds (`fastapi>=0.111`, no upper pin), so a blanket `uv lock --upgrade` can silently cross a major version. Always upgrade backend packages one at a time by name (`uv lock --upgrade-package <name>`), which is what `/housekeeping` does.

## Quality gates

```bash
make check   # ruff lint + mypy + pytest (backend), ESLint + Jest (frontend)
```

All gates must pass before committing. `/housekeeping` runs this and stops before making any commit-worthy claim if it fails.
