# Feature Specification: Migrate Dependency Management to uv

**Feature Branch**: `002-migrate-uv`

**Created**: 2026-05-27

**Status**: Draft

**Input**: Change app to use uv for dependencies instead of pip.

## Overview

Replace pip-based Python dependency management with uv across the Jobforce project. uv is a significantly faster package manager and resolver that maintains compatibility with the existing `pyproject.toml` format. The migration improves developer experience through faster installs, reproducible lockfiles, and a single tool that handles both virtual environment creation and package installation.

## User Scenarios & Testing

### User Story 1 — Developer installs the project for the first time (Priority: P1)

A developer clones the repo and sets up the backend in one command. With uv, `uv sync` creates the virtual environment and installs all dependencies from the lockfile automatically — no manual `python -m venv` + `pip install` step.

**Why this priority**: This is the most common onboarding path. Faster installs and a single command reduce friction for every new contributor.

**Independent Test**: After cloning a fresh checkout, run `uv sync` in `backend/` and confirm all dependencies install successfully and the app starts with `uv run uvicorn jobforce.main:app`.

**Acceptance Scenarios**:

1. **Given** a clean checkout with no `backend/.venv/`, **When** the developer runs `uv sync`, **Then** the virtual environment is created and all runtime and dev dependencies are installed within 30 seconds on a warm cache.
2. **Given** the virtual environment already exists, **When** `uv sync` is run again, **Then** it completes in under 5 seconds with no package changes (no-op).
3. **Given** the lockfile is present, **When** `uv sync` is run, **Then** exact package versions match the lockfile — no version drift.

---

### User Story 2 — Developer runs quality gates (Priority: P1)

`make check` continues to work identically after migration. The Makefile invokes ruff, mypy, and pytest through uv-managed tools without requiring the developer to manually activate a virtual environment.

**Why this priority**: Quality gates must not regress. CI depends on `make check` passing cleanly.

**Independent Test**: Run `make check` from `backend/` on a machine where only uv is installed (no pip). All lint, type-check, and test targets pass.

**Acceptance Scenarios**:

1. **Given** the uv environment is synced, **When** `make check` is run, **Then** all three gates (lint, typecheck, test) pass with zero errors.
2. **Given** a developer has not activated a venv, **When** `make lint` is run, **Then** the correct ruff binary from the uv environment is used automatically.

---

### User Story 3 — Developer adds or updates a dependency (Priority: P2)

A developer adds a new package to `pyproject.toml` and the lockfile is updated deterministically. Other developers pull the change and `uv sync` brings their environment in line with no manual steps.

**Why this priority**: Ongoing development requires adding packages. The lockfile workflow must be clearly documented.

**Independent Test**: Add a new dependency to `pyproject.toml`, run `uv lock`, commit both files. Another developer runs `uv sync` and the new package is present.

**Acceptance Scenarios**:

1. **Given** a new package is added to `pyproject.toml`, **When** `uv lock` is run, **Then** `uv.lock` is updated with the resolved version.
2. **Given** an updated `uv.lock` is pulled, **When** `uv sync` is run, **Then** the new package is installed automatically.

---

### User Story 4 — quickstart.md reflects uv workflow (Priority: P2)

The `quickstart.md` and `README.md` setup instructions reference `uv` rather than `pip install -e ".[dev]"`. A first-time user following the docs can set up the project without knowing pip.

**Why this priority**: Documentation drift causes onboarding failures. Docs must match the actual workflow.

**Independent Test**: Follow `quickstart.md` step by step on a machine with only uv installed. The app starts successfully.

**Acceptance Scenarios**:

1. **Given** the updated docs, **When** a developer follows the install section, **Then** the first command they run is `uv sync` (not `pip install`).
2. **Given** the updated README, **When** a developer reads the Prerequisites section, **Then** `uv` is listed as a prerequisite (replacing pip/venv mention).

---

### Edge Cases

- What happens if a developer has both uv and pip installed? uv takes precedence; pip is not invoked by any project tooling.
- What if `uv` is not installed on the developer's machine? `make install` or the quickstart provides the `uv` install command (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
- What if the lockfile `uv.lock` is missing (e.g., after a partial migration)? `uv sync` regenerates it from `pyproject.toml`.
- What about CI environments? The migration scope is local developer tooling; CI pipeline changes are out of scope unless CI already uses pip directly.

## Requirements

### Functional Requirements

- **FR-001**: The `backend/` directory MUST include a `uv.lock` lockfile generated from `pyproject.toml`.
- **FR-002**: `uv sync` run in `backend/` MUST install all runtime and dev dependencies and create `.venv/` automatically.
- **FR-003**: `make check` MUST continue to pass (lint, typecheck, test) after migration, invoking tools via `.venv/bin/` paths.
- **FR-004**: `make dev` MUST start the backend server using the uv-managed environment without requiring manual venv activation.
- **FR-005**: `make install` at the project root MUST install backend dependencies using `uv sync` rather than `pip install`.
- **FR-006**: `quickstart.md` and `README.md` MUST be updated to replace pip/venv instructions with `uv sync`.
- **FR-007**: The existing `pyproject.toml` dependency declarations MUST be preserved — no packages added or removed as part of this migration.
- **FR-008**: A developer MUST be able to add a new package by editing `pyproject.toml` and running `uv lock` to regenerate the lockfile.

### Key Entities

- **uv.lock**: The deterministic lockfile generated by uv, committed to version control alongside `pyproject.toml`.
- **pyproject.toml**: Existing dependency manifest — unchanged in terms of declared dependencies.
- **Makefile (backend)**: Updated to reference `.venv/bin/` tool paths (already done) and use `uv sync` for setup.
- **Makefile (root)**: `make install` target updated to call `uv sync`.

## Success Criteria

### Measurable Outcomes

- **SC-001**: `uv sync` in `backend/` completes in under 30 seconds on a clean install with a warm cache.
- **SC-002**: `make check` continues to pass with zero regressions — same 65 tests pass, 1 skipped.
- **SC-003**: All setup instructions in `quickstart.md` and `README.md` reference `uv` exclusively; zero references to `pip install -e` remain in developer-facing docs.
- **SC-004**: A `uv.lock` file is committed and reproducibly generates the same environment on any developer machine.
- **SC-005**: `make dev` starts the backend without manual venv activation on a freshly synced environment.

## Assumptions

- uv is already installed on the primary developer's machine (Warren's local environment, as noted in the quickstart prerequisites section referencing uv).
- The existing `pyproject.toml` is compatible with uv's PEP 517/518 resolver — no changes to dependency declarations are needed.
- CI pipelines (if any) are out of scope for this migration; only local developer tooling is updated.
- The `.venv/` directory path convention (`backend/.venv/`) is retained — uv places venvs in the same location by default.
- `uv run` is available as an alternative invocation pattern but Makefile will continue to use explicit `.venv/bin/` paths for clarity (already the pattern in the current Makefile).
