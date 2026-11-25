#!/usr/bin/env bash
# Expose the local stack to the internet via Cloudflare Tunnel.
#
# Quick mode (default, no account needed):
#   Gives a temporary *.trycloudflare.com URL that changes on restart.
#
# Permanent mode:
#   Set TUNNEL_NAME and TUNNEL_HOSTNAME in your shell, or see README.
set -e
cd "$(dirname "$0")/.."

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'

# ── Install cloudflared if missing ────────────────────��───────────────────────
if ! command -v cloudflared &>/dev/null; then
  echo -e "${CYAN}Installing cloudflared...${NC}"
  if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 \
      -o /tmp/cloudflared
    chmod +x /tmp/cloudflared
    sudo mv /tmp/cloudflared /usr/local/bin/cloudflared
  elif [[ "$OSTYPE" == "darwin"* ]]; then
    if command -v brew &>/dev/null; then
      brew install cloudflared
    else
      curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-darwin-amd64.tgz \
        | tar xz -C /usr/local/bin
    fi
  fi
  echo -e "${GREEN}✓ cloudflared installed${NC}"
fi

# ── Make sure the local stack is running ──────────────────────────────────────
if ! curl -sf http://localhost:8000/health &>/dev/null; then
  echo -e "${YELLOW}Stack is not running. Starting it first...${NC}"
  docker compose up -d
  sleep 5
fi

# ── Start tunnel ──────────────────────────────────────────────────────────────
if [[ -n "$TUNNEL_NAME" ]]; then
  # Permanent named tunnel (requires cloudflared login first)
  cloudflared tunnel run "$TUNNEL_NAME"
else
  # Quick temporary tunnel — URL changes on restart
  echo -e "${CYAN}Starting temporary Cloudflare Tunnel...${NC}"
  echo -e "${YELLOW}Your public URL will appear below. Share it with your client.${NC}"
  echo -e "${YELLOW}Note: this URL changes every time you restart the tunnel.${NC}"
  echo -e "${YELLOW}      See README for a permanent URL setup.${NC}"
  echo ""
  cloudflared tunnel --url http://localhost:80
fi
