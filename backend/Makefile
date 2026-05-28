.PHONY: check lint typecheck test dev

PYTHON := .venv/bin/python
RUFF := .venv/bin/ruff
MYPY := .venv/bin/mypy
PYTEST := .venv/bin/pytest
UVICORN := .venv/bin/uvicorn

check: lint typecheck test

lint:
	$(RUFF) check jobforce/ tests/
	$(RUFF) format --check jobforce/ tests/

typecheck:
	$(MYPY) jobforce/

test:
	$(PYTEST) tests/ -v

dev:
	$(UVICORN) jobforce.main:app --reload --port 8000
