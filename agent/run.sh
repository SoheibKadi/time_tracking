#!/usr/bin/env bash
# Launch the desktop agent (requires install.sh to have been run first).
cd "$(dirname "$0")"

if [ ! -d ".venv" ]; then
  echo "Virtual environment not found. Run ./install.sh first."
  exit 1
fi

if [ ! -f "agent.env" ]; then
  echo "agent.env not found. Copy agent.env.example to agent.env and edit it."
  exit 1
fi

source .venv/bin/activate
exec python main.py "$@"
