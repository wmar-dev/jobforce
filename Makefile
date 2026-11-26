.PHONY: dev stop check check-backend check-frontend check-extension test audit seed install openapi

dev:
	@echo "Starting Jobforce (backend + frontend)..."
	@cd backend && uv run uvicorn jobforce.main:app --reload --port 8000 &
	@cd frontend && npm run dev

stop:
	@echo "Stopping Jobforce dev servers..."
	@pkill -f "uvicorn" 2>/dev/null || true
	@pkill -f "next dev" 2>/dev/null || true

# The three components run concurrently. Each buffers its output and prints it
# as one block when done (macOS make 3.81 has no --output-sync).
check:
	@$(MAKE) -j3 --no-print-directory check-backend check-frontend check-extension

check-backend:
	@$(call gated,Backend,cd backend && $(MAKE) --no-print-directory check)

check-frontend:
	@$(call gated,Frontend,cd frontend && npm run check:api && npm run typecheck && npm run lint && npm run format:check && npm test)

check-extension:
	@$(call gated,Chrome extension,cd chrome-extension && npm run lint && npm test)

# $(call gated,<label>,<command>): run command, then print its output under a header.
gated = out=$$( ( $(2) ) 2>&1 ); rc=$$?; \
	echo "=== $(1) quality gates ==="; echo "$$out"; \
	if [ $$rc -ne 0 ]; then echo "=== $(1): FAILED ==="; fi; exit $$rc

test:
	@echo "=== Backend tests ==="
	@cd backend && $(MAKE) test
	@echo "=== Frontend tests ==="
	@cd frontend && npm test
	@echo "=== Chrome extension tests ==="
	@cd chrome-extension && npm test

audit:
	@echo "=== Frontend audit (prod deps) ==="
	@cd frontend && npm audit --omit=dev || true
	@echo "=== Chrome extension audit (prod deps) ==="
	@cd chrome-extension && npm audit --omit=dev || true
	@echo "=== Backend audit ==="
	@cd backend && uvx pip-audit || true

openapi:
	@echo "Regenerating backend/openapi.yaml and frontend API types..."
	@cd backend && $(MAKE) openapi
	@cd frontend && npm run gen:api

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
