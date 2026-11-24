# First-time server setup: creates .env, builds dashboard, starts the stack.
# Run once as: Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot)

Write-Host "=== Time Tracker — First-time setup ===" -ForegroundColor Cyan
Write-Host ""

# ── Docker check ──────────────────────────────────────────────────────────────
try { docker info 2>&1 | Out-Null }
catch {
    Write-Host "ERROR: Docker is not running. Start Docker Desktop and try again." -ForegroundColor Red
    exit 1
}
Write-Host "✓ Docker is running" -ForegroundColor Green

# ── Create .env ───────────────────────────────────────────────────────────────
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    $secret = python -c "import secrets; print(secrets.token_hex(32))"
    (Get-Content ".env") -replace "changeme_generate_a_real_secret", $secret | Set-Content ".env"
    Write-Host "✓ Created .env with auto-generated SECRET_KEY" -ForegroundColor Green
    Write-Host ""
    Write-Host "  IMPORTANT: Edit .env and change POSTGRES_PASSWORD, MINIO_ROOT_PASSWORD," -ForegroundColor Yellow
    Write-Host "             FIRST_ADMIN_EMAIL, and FIRST_ADMIN_PASSWORD before going live." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "  Press Enter to continue with defaults, or Ctrl+C to edit .env first"
} else {
    Write-Host "✓ .env already exists" -ForegroundColor Green
}

# ── Build dashboard ───────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Building dashboard (this may take a minute)..."
Push-Location dashboard
npm install --silent 2>$null
npm run build 2>$null | Select-Object -Last 3
Pop-Location
Write-Host "✓ Dashboard built" -ForegroundColor Green

# ── Start stack ───────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "Starting Docker Compose stack..."
docker compose up --build -d
Write-Host ""

# ── Wait for backend ──────────────────────────────────────────────────────────
Write-Host -NoNewline "Waiting for backend"
$ready = $false
for ($i = 1; $i -le 40; $i++) {
    try {
        Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null
        $ready = $true
        break
    } catch { Start-Sleep 2; Write-Host -NoNewline "." }
}
Write-Host ""
if (-not $ready) {
    Write-Host "Backend did not respond in time. Check: docker compose logs backend" -ForegroundColor Yellow
}

# ── Summary ───────────────────────────────────────────────────────────────────
Write-Host ""
Write-Host "=== Setup complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Dashboard : http://localhost" -ForegroundColor Green
Write-Host "  API docs  : http://localhost:8000/docs" -ForegroundColor Green
Write-Host "  MinIO     : http://localhost:9001" -ForegroundColor Green
Write-Host ""
Write-Host "  Admin credentials (from .env):"
Get-Content ".env" | Select-String "^FIRST_ADMIN_(EMAIL|PASSWORD)" | ForEach-Object { Write-Host "    $_" }
Write-Host ""
Write-Host "  Remember to change these credentials after first login!" -ForegroundColor Yellow
Write-Host ""
Pop-Location
