#!/usr/bin/env bash
# Deploy the React dashboard to Cloudflare Pages.
# Run this after setting RAILWAY_BACKEND_URL and CF_PAGES_PROJECT in your shell.
#
# Prerequisites (install once):
#   npm install -g wrangler
#   wrangler login
set -e
cd "$(dirname "$0")/.."

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'

# ── Validate inputs ───────────────────────────────────────────────────────────
if [[ -z "$RAILWAY_BACKEND_URL" ]]; then
  echo -e "${RED}ERROR: set RAILWAY_BACKEND_URL first.${NC}"
  echo "  Example: export RAILWAY_BACKEND_URL=https://time-tracker.railway.app"
  exit 1
fi

if [[ -z "$CF_PAGES_PROJECT" ]]; then
  echo -e "${YELLOW}CF_PAGES_PROJECT not set — defaulting to 'time-tracker'${NC}"
  CF_PAGES_PROJECT="time-tracker"
fi

# ── Build dashboard ───────────────────────────────────────────────────────────
echo -e "${CYAN}Building dashboard (pointing to $RAILWAY_BACKEND_URL)...${NC}"
cd dashboard
VITE_API_URL="$RAILWAY_BACKEND_URL" npm run build
cd ..
echo -e "${GREEN}✓ Dashboard built${NC}"

# ── Deploy to Cloudflare Pages ────────────────────────────────────────────────
echo -e "${CYAN}Deploying to Cloudflare Pages project '$CF_PAGES_PROJECT'...${NC}"
npx wrangler pages deploy dashboard/dist \
  --project-name "$CF_PAGES_PROJECT" \
  --commit-dirty=true

echo ""
echo -e "${GREEN}=== Deployment complete ===${NC}"
echo -e "Dashboard URL: ${GREEN}https://${CF_PAGES_PROJECT}.pages.dev${NC}"
echo ""
echo -e "${YELLOW}Don't forget to set BACKEND_CORS_ORIGINS on Railway:${NC}"
echo "  BACKEND_CORS_ORIGINS=[\"https://${CF_PAGES_PROJECT}.pages.dev\"]"
