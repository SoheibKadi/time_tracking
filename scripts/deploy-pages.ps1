# Deploy the React dashboard to Cloudflare Pages (Windows).
# Set $env:RAILWAY_BACKEND_URL and optionally $env:CF_PAGES_PROJECT first.
#
# Prerequisites (install once):
#   npm install -g wrangler
#   wrangler login
#Requires -Version 5.1
$ErrorActionPreference = "Stop"
Push-Location (Split-Path $PSScriptRoot)

if (-not $env:RAILWAY_BACKEND_URL) {
    Write-Host "ERROR: set RAILWAY_BACKEND_URL first." -ForegroundColor Red
    Write-Host "  Example: `$env:RAILWAY_BACKEND_URL = 'https://time-tracker.railway.app'"
    exit 1
}
if (-not $env:CF_PAGES_PROJECT) { $env:CF_PAGES_PROJECT = "time-tracker" }

# Build
Write-Host "Building dashboard (pointing to $($env:RAILWAY_BACKEND_URL))..." -ForegroundColor Cyan
Push-Location dashboard
$env:VITE_API_URL = $env:RAILWAY_BACKEND_URL
npm run build
Pop-Location
Write-Host "✓ Dashboard built" -ForegroundColor Green

# Deploy
Write-Host "Deploying to Cloudflare Pages project '$($env:CF_PAGES_PROJECT)'..." -ForegroundColor Cyan
npx wrangler pages deploy dashboard\dist --project-name $env:CF_PAGES_PROJECT --commit-dirty=true

Write-Host ""
Write-Host "=== Deployment complete ===" -ForegroundColor Green
Write-Host "Dashboard: https://$($env:CF_PAGES_PROJECT).pages.dev" -ForegroundColor Green
Write-Host ""
Write-Host "Don't forget to set BACKEND_CORS_ORIGINS on Railway:" -ForegroundColor Yellow
Write-Host "  BACKEND_CORS_ORIGINS=[`"https://$($env:CF_PAGES_PROJECT).pages.dev`"]"
Pop-Location
