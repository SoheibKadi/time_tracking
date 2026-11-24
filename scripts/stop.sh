#!/usr/bin/env bash
# Stop the Docker Compose stack (keeps data volumes).
cd "$(dirname "$0")/.."
docker compose down
echo "Stack stopped. Data volumes are preserved."
