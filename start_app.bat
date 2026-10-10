@echo off
title SupplyMind AI Enterprise Launcher
color 0B
echo ======================================================================
echo   SupplyMind AI Enterprise - B2B Dispute Resolution Engine
echo   Iniciando plataforma unificada (Backend FastAPI + Frontend React)
echo ======================================================================
echo.
echo [1/2] Verificando entorno virtual Python...
if exist .venv\Scripts\python.exe (
    set PY_EXE=.venv\Scripts\python.exe
) else (
    set PY_EXE=python
)

echo [2/2] Iniciando servidor FastAPI en http://localhost:8000 ...
echo       * Interfaz Web: http://localhost:8000
echo       * Swagger Docs: http://localhost:8000/docs
echo.
%PY_EXE% run_api.py
pause
