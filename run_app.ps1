# HealthSignal one-click development startup (Windows/PowerShell).
# Runs the FastAPI backend (port 8000) and the Vite frontend (port 5173).
# Prerequisites: .\.venv created (python -m venv .venv) with requirements installed,
# datasets trained (ml/scripts/train_all.py), sample images fetched
# (ml/scripts/fetch_samples.py), and demo data seeded (backend/scripts/seed_demo.py).
$root = $PSScriptRoot
$py = Join-Path $root ".venv\Scripts\python.exe"

Start-Process -FilePath $py -ArgumentList @("-m", "uvicorn", "app.main:app", "--port", "8000") -WorkingDirectory (Join-Path $root "backend")
Start-Sleep -Seconds 3
Start-Process -FilePath "cmd.exe" -ArgumentList @("/c", "npm run dev") -WorkingDirectory (Join-Path $root "frontend")

Write-Host "HealthSignal API: http://localhost:8000/api/health  (docs: /docs)"
Write-Host "HealthSignal UI:  http://localhost:5173"