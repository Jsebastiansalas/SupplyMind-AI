#!/usr/bin/env bash
# ==============================================================================
# SupplyMind AI Enterprise - Local Launcher (Linux / macOS)
# ==============================================================================

set -e

echo "======================================================================"
echo "  SupplyMind AI Enterprise - B2B Dispute Resolution Engine"
echo "  Iniciando plataforma unificada (Backend FastAPI + Frontend React)"
echo "======================================================================"
echo ""

echo "[1/2] Verificando entorno virtual Python..."
if [ -f ".venv/bin/python" ]; then
    PY_EXE=".venv/bin/python"
elif [ -f ".venv/Scripts/python.exe" ]; then
    PY_EXE=".venv/Scripts/python.exe"
else
    PY_EXE="python3"
fi

echo "[2/2] Iniciando servidor FastAPI en http://localhost:8000 ..."
echo "      * Interfaz Web: http://localhost:8000"
echo "      * Swagger Docs: http://localhost:8000/docs"
echo ""

$PY_EXE run_api.py
