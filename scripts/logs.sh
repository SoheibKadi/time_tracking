#!/usr/bin/env bash
# Tail logs from the stack. Pass a service name to filter, e.g.: ./logs.sh backend
cd "$(dirname "$0")/.."
docker compose logs -f ${1:-}
