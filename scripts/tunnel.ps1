# Expose the local stack to the internet via Cloudflare Tunnel (Windows).
#
# Quick mode (default):  temporary *.trycloudflare.com URL — changes on restart.
# Permanent mode:        set $env:TUNNEL_NAME before running, see README.
#Requires -Version 5.1

$cloudflaredExe = "$env:USERPROFILE\cloudflared.exe"

# ── Install cloudflared if missing ────────────────────────────────────────────
if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue) -and
    -not (Test-Path $cloudflaredExe)) {
    Write-Host "Installing cloudflared..." -ForegroundColor Cyan
    $dlUrl = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe"
    Invoke-WebRequest -Uri $dlUrl -OutFile $cloudflaredExe
    # Add to user PATH for this session and permanently
    $userPath = [System.Environment]::GetEnvironmentVariable("PATH", "User")
    if ($userPath -notlike "*$env:USERPROFILE*") {
        [System.Environment]::SetEnvironmentVariable("PATH", "$userPath;$env:USERPROFILE", "User")
    }
    $env:PATH += ";$env:USERPROFILE"
    Write-Host "✓ cloudflared installed to $cloudflaredExe" -ForegroundColor Green
}

$cf = if (Get-Command cloudflared -ErrorAction SilentlyContinue) { "cloudflared" } else { $cloudflaredExe }

# ── Make sure the local stack is running ──────────────────────────────────────
try { Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing | Out-Null }
catch {
    Write-Host "Stack not running. Starting it first..." -ForegroundColor Yellow
    docker compose up -d
    Start-Sleep 5
}

# ── Start tunnel ──────────────────────────────────────────────────────────────
if ($env:TUNNEL_NAME) {
    & $cf tunnel run $env:TUNNEL_NAME
} else {
    Write-Host ""
    Write-Host "Starting temporary Cloudflare Tunnel..." -ForegroundColor Cyan
    Write-Host "Your public URL will appear below — share it with your client." -ForegroundColor Yellow
    Write-Host "Note: this URL changes every time you restart the tunnel." -ForegroundColor Yellow
    Write-Host "      See README for a permanent URL setup." -ForegroundColor Yellow
    Write-Host ""
    & $cf tunnel --url http://localhost:80
}
