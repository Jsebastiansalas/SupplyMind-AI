@echo off
title SupplyMind AI - Produccion
echo ==========================================================
echo    SUPPLYMIND AI - INICIANDO ENTORNO DE PRODUCCION
echo ==========================================================

echo [1/3] Iniciando Servidor Backend FastAPI (Puerto 8000)...
start "SupplyMind Backend (FastAPI)" powershell -NoExit -Command "python -m uvicorn api.main:app --host 0.0.0.0 --port 8000"

echo [2/3] Iniciando Servidor Frontend Vite (Puerto 5173)...
start "SupplyMind Frontend (Vite)" powershell -NoExit -Command "cd frontend; npm run dev -- --host 0.0.0.0 --port 5173"

timeout /t 3 /nobreak >nul

echo [3/3] Abriendo navegador en http://localhost:5173...
start http://localhost:5173

echo ==========================================================
echo  Servidores iniciados con exito!
echo  - Frontend: http://localhost:5173
echo  - Backend:  http://localhost:8000
echo ==========================================================
echo Para reanudar el orquestador desatendido:
echo   python -u scripts/run_unattended_12h_batch.py
echo ==========================================================
pause
