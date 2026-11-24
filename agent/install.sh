#!/usr/bin/env bash
# Install the desktop agent dependencies into a local virtual environment.
set -e
cd "$(dirname "$0")"

echo "Installing Time Tracker Agent..."

if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 not found. Install Python 3.11+ and try again."
  exit 1
fi

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q

echo ""
echo "✓ Agent installed in .venv/"
echo ""
echo "Next steps:"
echo "  1. cp agent.env.example agent.env"
echo "  2. Edit agent.env — set SERVER_URL and CONTRACT_ID"
echo "  3. ./run.sh"
