#!/usr/bin/env bash
# ==============================================================================
# SupplyMind AI Enterprise - Docker Launcher (Linux / macOS)
# ==============================================================================

set -e

echo "======================================================================"
echo "  SupplyMind AI Enterprise - Docker Container Launcher"
echo "  Levantando plataforma unificada (FastAPI Backend + React 18 SPA)"
echo "======================================================================"
echo ""

echo "[1/3] Verificando estado del motor Docker..."
if ! docker info >/dev/null 2>&1; then
    echo "[ERROR] El servicio de Docker no está activo."
    echo "Por favor, inicia Docker Desktop o el daemon de Docker e intenta de nuevo."
    exit 1
fi

echo "[2/3] Compilando imagen y levantando contenedores con Docker Compose..."
docker compose up --build -d

echo ""
echo "======================================================================"
echo "  [ÉXITO] SupplyMind AI está corriendo en Docker:"
echo "  - Aplicación Web:       http://localhost:8000"
echo "  - Swagger API Docs:     http://localhost:8000/docs"
echo "  - API Healthcheck:      http://localhost:8000/api/health"
echo "======================================================================"
echo ""
echo "Para ver los logs en tiempo real: docker compose logs -f"
echo "Para detener la aplicación:       docker compose down"
echo ""
