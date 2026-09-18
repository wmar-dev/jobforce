.PHONY: dev stop check test seed install

dev:
	@echo "Starting Jobforce (backend + frontend)..."
	@cd backend && uv run uvicorn jobforce.main:app --reload --port 8000 &
	@cd frontend && npm run dev

stop:
	@echo "Stopping Jobforce dev servers..."
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "next dev" 2>/dev/null || true

check:
	@echo "=== Backend quality gates ==="
	@cd backend && $(MAKE) check
	@echo "=== Frontend quality gates ==="
	@cd frontend && npm run lint && npm test
	@echo "=== Chrome extension quality gates ==="
	@cd chrome-extension && npm test

test:
	@echo "=== Backend tests ==="
	@cd backend && $(MAKE) test
	@echo "=== Frontend tests ==="
	@cd frontend && npm test
	@echo "=== Chrome extension tests ==="
	@cd chrome-extension && npm test

seed:
	@echo "Seeding database from config.yaml..."
	@cd backend && uv run python -m jobforce.db.seed

install:
	@echo "Installing backend dependencies..."
	@cd backend && uv sync --extra dev
	@echo "Installing frontend dependencies..."
	@cd frontend && npm install
	@echo "Installing chrome-extension dependencies..."
	@cd chrome-extension && npm install
