# ==============================================================================
# SupplyMind AI Enterprise — Multi-Stage Production Dockerfile
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build React 18 Frontend Bundle (Vite + Tailwind CSS + Lucide Icons)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder

WORKDIR /app/frontend

# Copy dependency manifests
COPY frontend/package.json frontend/package-lock.json* ./

# Install dependencies
RUN npm install

# Copy frontend source files and configurations
COPY frontend/ ./

# Build production bundle into /app/frontend/dist
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Unified Backend & SPA Runtime (Python 3.11-slim + FastAPI)
# ------------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# System environment settings
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    HOST=0.0.0.0 \
    PORT=8000 \
    UVICORN_RELOAD=false

WORKDIR /app

# Install system dependencies:
# - curl: for Docker HEALTHCHECK
# - tesseract-ocr & tesseract-ocr-spa: OCR extraction for invoice/delivery receipts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tesseract-ocr \
    tesseract-ocr-spa \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application backend codebase, tests, scripts and assets
COPY agent/ ./agent/
COPY api/ ./api/
COPY config/ ./config/
COPY data/ ./data/
COPY scripts/ ./scripts/
COPY tests/ ./tests/
COPY tools/ ./tools/
COPY main.py .
COPY dashboard.py .
COPY run_api.py .
COPY .env.example .

# Ensure runtime directories exist
RUN mkdir -p /app/logs /app/reports /app/data/cases

# Copy compiled frontend from Stage 1 into /app/frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose unified port (FastAPI at /api, React SPA at /)
EXPOSE 8000

# Healthcheck to verify the server is responding to API requests
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Launch the unified server
CMD ["python", "run_api.py"]
