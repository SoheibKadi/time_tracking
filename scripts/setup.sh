#!/usr/bin/env bash
# First-time server setup: creates .env, builds dashboard, starts the stack.
set -e
cd "$(dirname "$0")/.."

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

echo -e "${CYAN}=== Time Tracker — First-time setup ===${NC}"
echo ""

# ── Docker check ──────────────────────────────────────────────────────────────
if ! docker info &>/dev/null; then
  echo -e "${RED}ERROR: Docker is not running. Start Docker Desktop and try again.${NC}"
  exit 1
fi
echo -e "${GREEN}✓ Docker is running${NC}"

# ── Create .env ───────────────────────────────────────────────────────────────
if [ ! -f .env ]; then
  cp .env.example .env
  SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null \
        || openssl rand -hex 32)
  # Replace placeholder secret key (portable sed for macOS + Linux)
  sed -i.bak "s|changeme_generate_a_real_secret|${SECRET}|" .env && rm -f .env.bak
  echo -e "${GREEN}✓ Created .env with auto-generated SECRET_KEY${NC}"
  echo -e "${YELLOW}"
  echo "  IMPORTANT: Edit .env and change POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD,"
  echo "             FIRST_ADMIN_EMAIL, and FIRST_ADMIN_PASSWORD before going live."
  echo -e "${NC}"
  read -p "  Press Enter to continue with defaults, or Ctrl+C to edit .env first... "
else
  echo -e "${GREEN}✓ .env already exists${NC}"
fi

# ── Build dashboard ───────────────────────────────────────────────────────────
echo ""
echo "Building dashboard (this may take a minute)..."
cd dashboard
npm install --silent 2>/dev/null
npm run build 2>/dev/null | tail -3
cd ..
echo -e "${GREEN}✓ Dashboard built${NC}"

# ── Start stack ───────────────────────────────────────────────────────────────
echo ""
echo "Starting Docker Compose stack..."
docker compose up --build -d
echo ""

# ── Wait for backend ─────────────────────────────────────────────────────────
echo -n "Waiting for backend to become ready"
for i in $(seq 1 40); do
  if curl -sf http://localhost:8000/health &>/dev/null; then
    echo ""
    break
  fi
  echo -n "."
  sleep 2
done

if ! curl -sf http://localhost:8000/health &>/dev/null; then
  echo -e "\n${YELLOW}Backend did not respond in time. Check logs: docker compose logs backend${NC}"
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo ""
echo -e "${CYAN}=== Setup complete ===${NC}"
echo ""
echo -e "  Dashboard : ${GREEN}http://localhost${NC}"
echo -e "  API docs  : ${GREEN}http://localhost:8000/docs${NC}"
echo -e "  MinIO     : ${GREEN}http://localhost:9001${NC}  (storage admin)"
echo ""
echo "  Admin credentials (from .env):"
grep -E "^FIRST_ADMIN_(EMAIL|PASSWORD)" .env | sed 's/^/    /'
echo ""
echo -e "${YELLOW}  Remember to change these credentials after first login!${NC}"
echo ""
