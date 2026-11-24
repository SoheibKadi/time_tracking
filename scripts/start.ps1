# Start the Docker Compose stack.
Push-Location (Split-Path $PSScriptRoot)
if (-not (Test-Path ".env")) { Write-Host "No .env found. Run .\scripts\setup.ps1 first." -ForegroundColor Red; exit 1 }
docker compose up -d
Write-Host "Stack started.  Dashboard: http://localhost" -ForegroundColor Green
Pop-Location
