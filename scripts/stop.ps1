# Stop the Docker Compose stack (keeps data volumes).
Push-Location (Split-Path $PSScriptRoot)
docker compose down
Write-Host "Stack stopped. Data volumes are preserved." -ForegroundColor Yellow
Pop-Location
