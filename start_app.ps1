# start_app.ps1 - Lanzador para PowerShell de SupplyMind AI Enterprise
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  SupplyMind AI Enterprise - B2B Dispute Resolution Engine" -ForegroundColor Yellow
Write-Host "  Iniciando plataforma unificada (Backend FastAPI + Frontend React)" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Cyan

$pyExe = if (Test-Path ".\.venv\Scripts\python.exe") { ".\.venv\Scripts\python.exe" } else { "python" }

Write-Host "`nServidor disponible en:" -ForegroundColor Green
Write-Host "  * Aplicacion Web: http://localhost:8000" -ForegroundColor Cyan
Write-Host "  * API Docs:       http://localhost:8000/docs`n" -ForegroundColor Cyan

& $pyExe run_api.py
