# HealthSignal one-click development startup (Windows/PowerShell).
# Runs the FastAPI backend and the Vite frontend.
#
#   .\run_app.ps1                                  # default: API 8000, UI 5173
#   .\run_app.ps1 -BackendPort 8001 -FrontendPort 5174
#
# Prerequisites: .\.venv created (python -m venv .venv) with requirements installed,
# datasets trained (ml/scripts/train_all.py), sample images fetched
# (ml/scripts/fetch_samples.py), and demo data seeded (backend/scripts/seed_demo.py).
param(
    [int]$BackendPort = 8000,
    [int]$FrontendPort = 5173
)

$root = $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

# The browser talks to the API through the Vite proxy, but the API also allows
# direct calls, so CORS has to know about the port this UI is served from.
$env:HS_ALLOW_ORIGINS = "http://localhost:$FrontendPort,http://127.0.0.1:$FrontendPort"
$env:VITE_API_TARGET = "http://127.0.0.1:$BackendPort"

Start-Process -FilePath $py -ArgumentList @(
    "-m", "uvicorn", "app.main:app",
    "--port", "$BackendPort", "--host", "127.0.0.1"
) -WorkingDirectory (Join-Path $root "backend")

Start-Sleep -Seconds 3
Start-Process -FilePath "cmd.exe" -ArgumentList @(
    "/c", "npm run dev -- --host 127.0.0.1 --port $FrontendPort --strictPort"
) -WorkingDirectory (Join-Path $root "frontend")

Write-Host "HealthSignal API: http://127.0.0.1:$BackendPort/api/health  (docs: /docs)"
Write-Host "HealthSignal UI:  http://127.0.0.1:$FrontendPort"
Write-Host "Demo login:       patient.demo@healthsignal.dev / healthsignal-demo-pw-2026"
