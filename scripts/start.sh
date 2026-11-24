#!/usr/bin/env bash
# Start the Docker Compose stack.
set -e
cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
  echo "No .env found. Run ./scripts/setup.sh first."
  exit 1
fi

docker compose up -d
echo "Stack started."
echo "  Dashboard : http://localhost"
echo "  API       : http://localhost:8000"
