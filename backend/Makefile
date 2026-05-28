.PHONY: check lint typecheck test dev sync

PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest

check: lint typecheck test

lint:
	$(RUFF) check jobforce/ tests/
	$(RUFF) format --check jobforce/ tests/

typecheck:
	$(MYPY) jobforce/

test:
	$(PYTEST) tests/ -v

sync:
	uv sync --extra dev

dev:
	uv run uvicorn jobforce.main:app --reload --port 8000
