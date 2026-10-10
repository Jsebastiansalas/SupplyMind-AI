@echo off
title SupplyMind AI Enterprise - Docker Launcher
color 0A
echo ======================================================================
echo   SupplyMind AI Enterprise - Docker Container Launcher
echo   Levantando plataforma unificada (FastAPI Backend + React 18 SPA)
echo ======================================================================
echo.

echo [1/3] Verificando estado del motor Docker...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] El servicio de Docker no esta activo.
    echo Asegurate de abrir Docker Desktop y esperar a que inicialice.
    echo.
    pause
    exit /b 1
)

echo [2/3] Compilando imagen y levantando contenedores...
docker compose up --build -d

if %errorlevel% equ 0 (
    echo.
    echo ======================================================================
    echo   [EXITO] SupplyMind AI esta corriendo en Docker:
    echo   - Aplicacion Web:       http://localhost:8000
    echo   - Swagger API Docs:     http://localhost:8000/docs
    echo   - API Healthcheck:      http://localhost:8000/api/health
    echo ======================================================================
    echo.
    echo Para ver los logs en tiempo real: docker compose logs -f
    echo Para detener la aplicacion:       docker compose down
    echo.
) else (
    echo [ERROR] Hubo un problema al levantar los contenedores con Docker Compose.
)

pause
