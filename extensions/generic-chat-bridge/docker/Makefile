# OSS Chat Platform E2E Testing Makefile
# Usage: make up, make seed-rc, make test-rc-ui, etc.

.PHONY: help up down logs seed-rc seed-zulip test-ready test-rc-ui test-zulip-ui clean

help: ## Show this help message
	@echo "OSS Chat Platform E2E Testing Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

up: ## Start all Docker services (Rocket.Chat + Zulip)
	docker compose up -d
	@echo "Services starting... Check status with 'make logs' or 'docker compose ps'"
	@echo "Rocket.Chat: http://127.0.0.1:3000"
	@echo "Zulip: http://127.0.0.1:9991 (may take 3-10 min to initialize)"

down: ## Stop all Docker services
	docker compose down

clean: ## Stop services and remove volumes (fresh restart)
	docker compose down -v
	@echo "All services stopped and data volumes removed"

logs: ## Show logs for all services
	docker compose logs -f

logs-rc: ## Show Rocket.Chat logs
	docker compose logs -f rocketchat

logs-zulip: ## Show Zulip logs
	docker compose logs -f zulip

logs-mongo: ## Show MongoDB logs
	docker compose logs -f mongo

seed-rc: ## Seed Rocket.Chat with test users and #e2e channel
	@echo "Seeding Rocket.Chat..."
	@echo "Note: Complete the admin setup wizard at http://127.0.0.1:3000 first"
	@echo "Then update .env with your admin credentials"
	node seed-rocketchat.mjs

seed-zulip: ## Seed Zulip with test users and e2e stream
	@echo "Seeding Zulip..."
	@echo "Note: Complete initial setup at http://127.0.0.1:9991 and get API key first"
	@echo "Usage: ZULIP_EMAIL=admin@example.com ZULIP_API_KEY=your_key make seed-zulip"
	node seed-zulip.mjs

test-ready: ## Test if OSS services are responding
	cd ../tests/e2e && RUN_OSS=1 npx playwright test docker-readiness.spec.ts -c playwright.config.ts

test-rc-ui: ## Run Rocket.Chat UI E2E test with browser extension
	@echo "Running Rocket.Chat UI test..."
	cd ../tests/e2e && \
	export EXTENSION_PATH=$$(realpath ../../) && \
	RUN_OSS=1 npx playwright test rocketchat-ui.spec.ts -c playwright.config.ts

test-zulip-ui: ## Run Zulip UI E2E test with browser extension
	@echo "Running Zulip UI test..."
	cd ../tests/e2e && \
	export EXTENSION_PATH=$$(realpath ../../) && \
	RUN_OSS=1 ZULIP_SEEDED=1 npx playwright test zulip-ui.spec.ts -c playwright.config.ts

test-all-oss: ## Run all OSS E2E tests (readiness + UI tests)
	@echo "Running complete OSS test suite..."
	cd ../tests/e2e && \
	export EXTENSION_PATH=$$(realpath ../../) && \
	RUN_OSS=1 npx playwright test docker-readiness.spec.ts rocketchat-ui.spec.ts -c playwright.config.ts
	@echo "Note: Add ZULIP_SEEDED=1 and include zulip-ui.spec.ts if Zulip is configured"

status: ## Show service status
	docker compose ps

quick-start: ## Quick setup guide
	@echo "Quick Start Guide:"
	@echo "1. make up              # Start services"
	@echo "2. Visit http://127.0.0.1:3000 and complete Rocket.Chat setup"
	@echo "3. Edit .env with your admin credentials"
	@echo "4. make seed-rc         # Create test users and channel"
	@echo "5. make test-rc-ui      # Run browser extension E2E test"
	@echo ""
	@echo "For Zulip (optional):"
	@echo "6. Visit http://127.0.0.1:9991 and complete setup"
	@echo "7. ZULIP_EMAIL=you@example.com ZULIP_API_KEY=key make seed-zulip"
	@echo "8. make test-zulip-ui"