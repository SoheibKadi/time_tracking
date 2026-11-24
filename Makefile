.PHONY: setup start stop logs update help

help:
	@echo "Time Tracker — available targets:"
	@echo "  make setup    First-time setup (creates .env, builds dashboard, starts stack)"
	@echo "  make start    Start the Docker stack"
	@echo "  make stop     Stop the Docker stack"
	@echo "  make logs     Tail all container logs  (SERVICE=backend to filter)"
	@echo "  make update   Pull latest code and restart"

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
