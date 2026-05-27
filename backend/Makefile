.PHONY: check lint typecheck test dev

check: lint typecheck test

lint:
	ruff check jobforce/ tests/
	ruff format --check jobforce/ tests/

typecheck:
	mypy jobforce/

test:
	pytest tests/ -v

dev:
	uvicorn jobforce.main:app --reload --port 8000
