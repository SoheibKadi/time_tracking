.PHONY: setup start stop logs update help

help:
	@echo "Time Tracker — available targets:"
	@echo "  make setup         First-time setup (creates .env, builds dashboard, starts stack)"
	@echo "  make start         Start the Docker stack"
	@echo "  make stop          Stop the Docker stack"
	@echo "  make logs          Tail all container logs  (SERVICE=backend to filter)"
	@echo "  make update        Pull latest code and restart"
	@echo "  make tunnel        Expose local stack via Cloudflare Tunnel (Option A)"
	@echo "  make deploy-pages  Deploy dashboard to Cloudflare Pages (Option B)"

setup:
	@chmod +x scripts/*.sh agent/*.sh
	./scripts/setup.sh

start:
	./scripts/start.sh

stop:
	./scripts/stop.sh

logs:
	docker compose logs -f $(SERVICE)

update:
	./scripts/update.sh

tunnel:
	@chmod +x scripts/tunnel.sh
	./scripts/tunnel.sh

deploy-pages:
	@chmod +x scripts/deploy-pages.sh
	RAILWAY_BACKEND_URL=$(RAILWAY_BACKEND_URL) CF_PAGES_PROJECT=$(CF_PAGES_PROJECT) ./scripts/deploy-pages.sh
