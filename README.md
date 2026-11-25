# Time Tracker

> Self-hosted freelance time tracker with screenshots, activity metrics, and a shareable client dashboard.

**© 2026 Soheyb Kadi — All rights reserved.** Source is publicly visible for reference; use, distribution, and hosting as a service require written permission. See [LICENSE](./LICENSE).

Inspired by the Upwork Time Tracker. You run it on your own VPS or home server. Your client gets a live read-only link.
---

## Features

| Feature | Detail |
|---|---|
| **Desktop agent** | Windows (primary), macOS, Linux — system-tray app |
| **Screenshots** | Random interval per 10-min window; SHA-256 tamper detection; 60s grace period to delete before upload |
| **Activity metrics** | Keystrokes + mouse events counted per 60s sample; activity level 0–10 |
| **Manual override** | Mark any window as "In a meeting / watching tutorial" with a note |
| **Idle detection** | Prompt after 5 min of silence; auto-pause after 2 min no response |
| **Live client link** | Share a URL — client sees screenshots and activity in real time (WebSocket push) |
| **Client disputes** | Client flags a window; you accept or reject from the dashboard |
| **Invoice PDF** | Generate a PDF invoice from billable hours for any date range |
| **App blocklist** | Blur screenshots when a password manager or other sensitive app is in focus |
| **Multi-monitor** | All monitors captured as one stitched image |
| **Admin panel** | User management, invite users, audit log |
| **PWA** | Client share page is installable as a mobile app |
| **Multi-tenant** | Optional self-registration (disabled by default) |

---

## Architecture

```
┌─────────────────────────┐
│   Desktop Agent         │  Windows / macOS / Linux
│   Python + PyQt6        │  system-tray app
└──────────┬──────────────┘
           │  HTTPS
┌──────────▼──────────────┐
│   Backend Server        │  Docker Compose on any VPS
│   FastAPI + PostgreSQL  │
│   MinIO (screenshots)   │
└──────────┬──────────────┘
           │
┌──────────▼──────────────┐
│   Web Dashboard         │  React SPA — served by Nginx
│   /dashboard  (worker)  │
│   /share/:token (client)│  ← send this URL to your client
└─────────────────────────┘
```

---

## Quick Start

### Prerequisites

| Component | Requirement |
|---|---|
| **Server** | Docker Desktop (Windows/macOS) or Docker + Compose plugin (Linux) |
| **Agent** | Python 3.11+, Windows 10/11 (primary) |
| **Client** | Any modern browser |

---

### Step 1 — Set up the server

```bash
git clone https://github.com/SoheibKadi/time_tracking.git
cd time_tracking
```

**Linux / macOS:**
```bash
chmod +x scripts/*.sh agent/*.sh
./scripts/setup.sh
```

**Windows (PowerShell — run as Administrator once to allow scripts):**
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\setup.ps1
```

The setup script:
1. Copies `.env.example` → `.env` and auto-generates a secure `SECRET_KEY`
2. Builds the React dashboard (`npm run build`)
3. Starts the full Docker stack
4. Waits for the backend to become healthy
5. Prints the dashboard URL and default admin credentials

> **Change the admin password** shown at the end of setup before going live.

---

### Step 2 — Log in and create a contract

1. Open **http://your-server** (or `http://localhost` on the same machine)
2. Log in with the admin credentials printed by the setup script
3. Go to **Contracts → New Contract**
4. Fill in: title, hourly rate, your client's name and email
5. Copy the **Share Link** from the contract card — send it to your client

---

### Step 3 — Set up the desktop agent

**Windows:**
```bat
cd agent
install.bat
copy agent.env.example agent.env
rem Edit agent.env — set SERVER_URL and CONTRACT_ID
run.bat
```

**macOS / Linux:**
```bash
cd agent
./install.sh
cp agent.env.example agent.env
# Edit agent.env — set SERVER_URL and CONTRACT_ID
./run.sh
```

A **Login dialog** appears on first run if `ACCESS_TOKEN` is empty. Enter your email and password — the token is saved automatically to `agent.env`.

> **Finding the CONTRACT_ID:** open the contract in the dashboard — the UUID is in the page URL (`/dashboard/contracts/<uuid>`).

---

### Step 4 — Start tracking

Right-click the system tray icon → **▶ Start tracking**

Your client can open the share link in any browser and see a live feed of your work.

---

## Server management

| Task | Linux / macOS | Windows |
|---|---|---|
| Start stack | `./scripts/start.sh` | `.\scripts\start.ps1` |
| Stop stack | `./scripts/stop.sh` | `.\scripts\stop.ps1` |
| View logs | `./scripts/logs.sh` | `docker compose logs -f` |
| Update to latest | `./scripts/update.sh` | pull + re-run setup |
| Start tunnel | `./scripts/tunnel.sh` | `.\scripts\tunnel.ps1` |

---

## Deployment Options

The Quick Start above runs everything on a server you control (VPS or cloud VM). Two
additional free options are supported when you don't want to maintain a server.

---

### Option A — Local machine + Cloudflare Tunnel (free)

Run the entire stack on the **same Windows PC you use for tracking**, then expose it
to the internet with [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/). No VPS, no port forwarding, no cost.

```
Your Windows PC
  ├─ Desktop Agent (tracking)
  ├─ Docker Desktop (backend + dashboard)
  └─ cloudflared ──→ https://abc123.trycloudflare.com ──→ Client's browser
```

**Setup (10 minutes):**

1. Run `./scripts/setup.sh` (or `.\scripts\setup.ps1`) to start the local stack.
2. Run the tunnel:
   ```bash
   # Linux / macOS
   ./scripts/tunnel.sh

   # Windows
   .\scripts\tunnel.ps1
   ```
   `cloudflared` is downloaded automatically if not installed.

3. A URL like `https://abc123.trycloudflare.com` appears. Share it with your client.

**Limitation:** the client link is offline whenever your machine is off. The URL also
changes on restart in quick mode (see below for a permanent URL).

#### Permanent URL (optional)

For a stable URL that doesn't change between restarts:

1. Create a free [Cloudflare account](https://cloudflare.com) and add your domain (or use a free `*.pages.dev` subdomain).
2. Install and authenticate `cloudflared`:
   ```bash
   cloudflared login
   cloudflared tunnel create time-tracker
   ```
3. Set `TUNNEL_NAME=time-tracker` in your shell before running the tunnel script.

---

### Option B — Cloud: Railway + Cloudflare R2 + Pages (free tier)

Always-on cloud deployment using three free services — no VPS required.

| Service | Purpose | Free tier |
|---|---|---|
| [Railway](https://railway.app) | Backend (FastAPI + PostgreSQL) | $5 credit/month |
| [Cloudflare R2](https://cloudflare.com/products/r2/) | Screenshot storage | 10 GB / 1M ops free |
| [Cloudflare Pages](https://pages.cloudflare.com) | Dashboard (static hosting) | Unlimited requests free |

**Architecture:**

```
Desktop Agent ──HTTPS──→ Railway (FastAPI + PostgreSQL)
                               │
                        Cloudflare R2 (screenshots)
                               │
Client browser ──→ Cloudflare Pages (dashboard)
```

#### Step 1 — Set up Cloudflare R2

1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com) → **R2** → **Create bucket** → name it `timetracker`.
2. Go to **R2 → Manage R2 API Tokens** → **Create API Token** (Object Read & Write).
3. Note your **Account ID**, **Access Key ID**, and **Secret Access Key**.

#### Step 2 — Deploy the backend to Railway

1. Install the Railway CLI and log in:
   ```bash
   npm install -g @railway/cli
   railway login
   ```

2. From the project root, initialise and deploy:
   ```bash
   railway init          # creates a new project
   railway up            # builds and deploys backend/Dockerfile
   ```

3. In the [Railway dashboard](https://railway.app/dashboard), open your project and:
   - Add a **PostgreSQL** plugin — Railway auto-sets `DATABASE_URL`.
   - Add these environment variables:

   | Variable | Value |
   |---|---|
   | `SECRET_KEY` | `openssl rand -hex 32` output |
   | `MINIO_ENDPOINT` | `https://<ACCOUNT_ID>.r2.cloudflarestorage.com` |
   | `AWS_ACCESS_KEY_ID` | Your R2 Access Key ID |
   | `AWS_SECRET_ACCESS_KEY` | Your R2 Secret Access Key |
   | `MINIO_BUCKET` | `timetracker` |
   | `FIRST_ADMIN_EMAIL` | your email |
   | `FIRST_ADMIN_PASSWORD` | a strong password |
   | `ALLOW_REGISTRATION` | `false` |

4. Note the Railway public URL (e.g. `https://time-tracker.railway.app`).

#### Step 3 — Deploy the dashboard to Cloudflare Pages

1. Install `wrangler` and log in:
   ```bash
   npm install -g wrangler
   wrangler login
   ```

2. Build and deploy:
   ```bash
   # Linux / macOS
   export RAILWAY_BACKEND_URL=https://time-tracker.railway.app
   ./scripts/deploy-pages.sh

   # Windows
   $env:RAILWAY_BACKEND_URL = "https://time-tracker.railway.app"
   .\scripts\deploy-pages.ps1
   ```

3. Your dashboard is live at `https://time-tracker.pages.dev`.

#### Step 4 — Allow CORS on Railway

Back in the Railway dashboard, add one more environment variable:

```
BACKEND_CORS_ORIGINS=["https://time-tracker.pages.dev"]
```

Railway redeploys automatically.

#### Step 5 — Point the agent at Railway

In `agent/agent.env`, set:
```
SERVER_URL=https://time-tracker.railway.app
```

---

## Configuration

### Server (`.env`)

| Variable | Default | Description |
|---|---|---|
| `SECRET_KEY` | — | **Required.** JWT signing key. Auto-generated by setup. |
| `POSTGRES_PASSWORD` | `changeme` | PostgreSQL password |
| `MINIO_ROOT_PASSWORD` | `changeme` | MinIO admin password |
| `FIRST_ADMIN_EMAIL` | `admin@example.com` | Seed admin account email |
| `FIRST_ADMIN_PASSWORD` | `changeme` | Seed admin account password |
| `ALLOW_REGISTRATION` | `false` | Set `true` to allow public self-registration |
| `SMTP_HOST` | _(empty)_ | SMTP server for dispute email notifications |

### Agent (`agent/agent.env`)

| Variable | Default | Description |
|---|---|---|
| `SERVER_URL` | `http://localhost:8000` | Backend base URL |
| `CONTRACT_ID` | — | **Required.** UUID of your active contract |
| `CAPTURE_ALL_MONITORS` | `true` | Capture all monitors (`false` = primary only) |
| `IDLE_TIMEOUT_MIN` | `5` | Minutes of zero activity before idle prompt |
| `IDLE_AUTOPAUSE_SEC` | `120` | Seconds to auto-pause after idle prompt |
| `SCREENSHOT_INTERVAL_MIN` | `10` | Window duration in minutes |
| `ACTIVITY_SCALE_FACTOR` | `150` | Denominator in activity level formula |

---

## Platform notes

### macOS
- **Screen Recording** permission required for screenshots: System Settings → Privacy & Security → Screen Recording
- **Accessibility** permission required for keyboard/mouse tracking: System Settings → Privacy & Security → Accessibility
- The agent shows tray notifications if permissions are missing

### Linux
- Works best under **X11**. Wayland does not support global keyboard/mouse hooks — activity tracking gracefully falls back (screenshots still work)
- `xdotool` needed for foreground window detection (blocklist feature): `sudo apt install xdotool`

### Windows
- No special permissions needed
- Tested on Windows 10 and Windows 11

---

## Development

### Backend (without Docker)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://timetracker:changeme@localhost:5432/timetracker
alembic upgrade head
uvicorn app.main:app --reload
# API docs at http://localhost:8000/docs
```

### Dashboard (dev server)

```bash
cd dashboard
npm install
npm run dev        # hot-reload dev server at http://localhost:5173
npm run build      # production build → dist/
```

### Desktop agent

```bash
cd agent
pip install -r requirements.txt
cp agent.env.example agent.env   # edit with your settings
python main.py
```

### Building a Windows executable

```bash
cd agent
pip install pyinstaller
pyinstaller --onefile --windowed --name TimeTrackerAgent main.py
# Output: dist/TimeTrackerAgent.exe
```

---

## See also

- [SPEC.md](./SPEC.md) — full product specification, architecture decisions, data models, and API surface
