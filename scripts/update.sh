#!/usr/bin/env bash
# Pull latest code, rebuild the dashboard, and restart the stack.
set -e
cd "$(dirname "$0")/.."

echo "Pulling latest changes..."
git pull

echo "Building dashboard..."
cd dashboard
npm install --silent
npm run build 2>/dev/null | tail -3
cd ..

echo "Restarting stack..."
docker compose up --build -d

echo "Update complete."
