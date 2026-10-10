<#
.SYNOPSIS
    Lanzador de SupplyMind AI Enterprise en contenedores Docker para PowerShell.
#>

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "  SupplyMind AI Enterprise - Docker Container Launcher" -ForegroundColor Cyan
Write-Host "  Levantando plataforma unificada (FastAPI Backend + React 18 SPA)" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/3] Verificando estado del motor Docker..." -ForegroundColor Yellow
$dockerCheck = docker info 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] El servicio de Docker no está activo en esta máquina." -ForegroundColor Red
    Write-Host "Por favor inicia Docker Desktop y vuelve a ejecutar este script." -ForegroundColor DarkYellow
    Read-Host "Presiona Enter para salir..."
    exit 1
}

Write-Host "[2/3] Compilando imagen y levantando contenedores en segundo plano..." -ForegroundColor Yellow
docker compose up --build -d

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host "  [ÉXITO] SupplyMind AI está corriendo en Docker:" -ForegroundColor Green
    Write-Host "  - Aplicación Web:       http://localhost:8000" -ForegroundColor Green
    Write-Host "  - Swagger API Docs:     http://localhost:8000/docs" -ForegroundColor Green
    Write-Host "  - API Healthcheck:      http://localhost:8000/api/health" -ForegroundColor Green
    Write-Host "======================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Comandos útiles:" -ForegroundColor Cyan
    Write-Host "  - Ver logs en vivo: docker compose logs -f" -ForegroundColor Gray
    Write-Host "  - Detener servicio: docker compose down" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] Falló la ejecución de 'docker compose up --build -d'." -ForegroundColor Red
}

Read-Host "Presiona Enter para continuar..."
