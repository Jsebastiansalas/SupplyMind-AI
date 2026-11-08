# scripts/start_production.ps1
# Script para iniciar todos los servicios de producción de SupplyMind AI

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   SUPPLYMIND AI - INICIANDO ENTORNO DE PRODUCCION        " -ForegroundColor Yellow
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Iniciar Servidor Backend FastAPI en segundo plano (Puerto 8000)
Write-Host "`n[1/3] Iniciando Servidor Backend FastAPI (Puerto 8000)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

# 2. Iniciar Servidor Frontend Vite en segundo plano (Puerto 5173)
Write-Host "[2/3] Iniciando Servidor Frontend Vite (Puerto 5173)..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev -- --host 0.0.0.0 --port 5173"

# 3. Esperar 3 segundos para que los servidores levanten
Start-Sleep -Seconds 3

# 4. Abrir la interfaz en el navegador
Write-Host "[3/3] Abriendo navegador en http://localhost:5173..." -ForegroundColor Green
Start-Process "http://localhost:5173"

Write-Host "`n==========================================================" -ForegroundColor Cyan
Write-Host " Entorno de Produccion Activo:" -ForegroundColor Yellow
Write-Host "  * Frontend UI:     http://localhost:5173" -ForegroundColor White
Write-Host "  * Backend API:     http://localhost:8000" -ForegroundColor White
Write-Host "  * Documentacion:   http://localhost:8000/docs" -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "`nPara reanudar el orquestador desatendido de 1,024 unidades, ejecuta:" -ForegroundColor Magenta
Write-Host "  python -u scripts/run_unattended_12h_batch.py" -ForegroundColor Yellow
Write-Host "o en modo acelerado:" -ForegroundColor Magenta
Write-Host "  python -u scripts/run_unattended_12h_batch.py --no-pacing" -ForegroundColor Yellow
