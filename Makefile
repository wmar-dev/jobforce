.PHONY: dev check seed install

dev:
	@echo "Starting Jobforce (backend + frontend)..."
	@cd backend && uvicorn jobforce.main:app --reload --port 8000 &
	@cd frontend && npm run dev

check:
	@echo "=== Backend quality gates ==="
	@cd backend && $(MAKE) check
	@echo "=== Frontend quality gates ==="
	@cd frontend && npm run lint && npm test

seed:
	@echo "Seeding database from config.yaml..."
	@cd backend && python -m jobforce.db.seed

install:
	@echo "Installing backend dependencies..."
	@cd backend && pip install -e ".[dev]"
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
